"""Americas regional chapter — narrative-first regional case study."""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from app.stage2 import elevation_topography as etopo
from app.stage2 import region_data as rd
from app.stage2.region_shell import (
    chapter_footer_full_arc,
    inject_page_theme_variant,
    inject_region_page_css,
    region_hero,
    section_divider,
    section_title,
    sidebar_chapters,
)

AMERICAS_MAP_BRIDGE_HTML = """
<div class="s2-bridge americas-map-bridge">
  <p>The home map placed the Americas in the U.S. import picture. From here: scale and trade, then terrain, then what the
  cup averages in this sample can actually support.</p>
</div>
"""


def _country_altitude_context(americas_cup: pd.DataFrame, elev_ctx: pd.DataFrame) -> pd.DataFrame:
    cup = (
        americas_cup.dropna(subset=["country_of_origin", "altitude"])
        .groupby("country_of_origin", as_index=False)
        .agg(
            lot_altitude_p25=("altitude", lambda s: float(np.percentile(s, 25))),
            lot_altitude_median=("altitude", "median"),
            lot_altitude_p75=("altitude", lambda s: float(np.percentile(s, 75))),
            lots=("altitude", "count"),
        )
        .rename(columns={"country_of_origin": "country"})
    )
    if elev_ctx.empty:
        return cup
    cols = [c for c in ["country", "representative_elevation_m"] if c in elev_ctx.columns]
    return cup.merge(elev_ctx[cols], on="country", how="left")


def _lot_altitudes_long(americas_cup: pd.DataFrame, countries: list[str]) -> pd.DataFrame:
    """Per-lot altitudes for box plots (Americas elevation comparison)."""
    cup = americas_cup.dropna(subset=["country_of_origin", "altitude"])
    if cup.empty or not countries:
        return pd.DataFrame(columns=["country", "altitude"])
    cup = cup[cup["country_of_origin"].isin(countries)]
    # Select only origin + altitude so an existing ``country`` column on the frame cannot collide
    # after rename (duplicate ``country`` names break ``groupby("country")``).
    out = cup[["country_of_origin", "altitude"]].copy()
    return out.rename(columns={"country_of_origin": "country"})


def _country_flavor_summary(americas_cup: pd.DataFrame) -> pd.DataFrame:
    """Per-country means for cup profile views (lot-level cupping sample, not a national census)."""
    cols = [
        "country_of_origin",
        "altitude",
        "total_cup_points",
        "acidity",
        "body",
        "flavor",
        "balance",
        "overall",
    ]
    sub = americas_cup.dropna(subset=["country_of_origin"])
    existing = [c for c in cols if c in sub.columns]
    sub = sub[existing].copy()
    agg: dict[str, tuple[str, str]] = {"lots": ("country_of_origin", "count")}
    if "altitude" in sub.columns:
        agg["median_altitude"] = ("altitude", "median")
    if "total_cup_points" in sub.columns:
        agg["mean_total_points"] = ("total_cup_points", "mean")
    for c in ("acidity", "flavor", "body", "balance", "overall"):
        if c in sub.columns:
            agg[c] = (c, "mean")
    return sub.groupby("country_of_origin", as_index=False).agg(**agg).sort_values("lots", ascending=False)


def _americas_sensory_heatmap_figure(keep: pd.DataFrame):
    """Country × sensory heatmap; color encodes deviation from Americas mean in this slice."""
    import plotly.graph_objects as go

    from app.plotly_theme import plotly_layout_base

    metric_cols = [c for c in ("acidity", "flavor", "body", "balance", "overall") if c in keep.columns]
    metric_cols = [c for c in metric_cols if keep[c].notna().any()]
    if len(metric_cols) < 2:
        return None

    display = {
        "acidity": "Acidity",
        "flavor": "Flavor",
        "body": "Body",
        "balance": "Balance",
        "overall": "Overall",
    }
    order = keep["country_of_origin"].tolist()
    raw = (
        keep.set_index("country_of_origin")[metric_cols]
        .astype(float)
        .reindex(order)
        .dropna(axis=1, how="all")
    )
    if raw.shape[1] < 2:
        return None
    raw = raw.dropna(axis=0, how="all")
    if raw.shape[0] < 2:
        return None

    col_means = raw.mean(axis=0, skipna=True)
    centered = raw.subtract(col_means, axis=1)
    vmax = float(np.nanmax(np.abs(centered.values)))
    if not np.isfinite(vmax) or vmax < 1e-6:
        vmax = 0.15
    # Stretch color scale slightly past data so small deviations read as modest, not neon.
    z_span = float(max(vmax * 1.2, 1e-6))

    x_labels = [display[c] for c in raw.columns]
    z = centered.values
    text = np.round(raw.values.astype(float), 2)
    fig = go.Figure(
        data=go.Heatmap(
            z=z,
            x=x_labels,
            y=raw.index.tolist(),
            text=text,
            texttemplate="%{text:.2f}",
            textfont={"size": 10, "color": "#e8ecf1"},
            colorscale=[
                [0.0, "#4d6a94"],
                [0.5, "#1e293b"],
                [1.0, "#c86a4a"],
            ],
            zmid=0.0,
            zmin=-z_span,
            zmax=z_span,
            hovertemplate=(
                "<b>%{y}</b> · %{x}<br>"
                "Mean (this slice): %{text:.2f}<br>"
                "Δ vs Americas mean: %{z:+.2f}<extra></extra>"
            ),
            colorbar=dict(
                title=dict(text="Δ vs mean", font=dict(size=9, color="#94a3b8")),
                tickfont=dict(size=10, color="#94a3b8"),
                len=0.72,
                thickness=12,
            ),
        )
    )
    row_h = max(40, min(48, 320 // max(raw.shape[0], 1)))
    fig.update_layout(
        **plotly_layout_base(height=64 + row_h * raw.shape[0]),
        title=dict(
            text="Country means vs Americas average (small deviations)",
            font=dict(size=11, color="#cbd5e1"),
        ),
        xaxis=dict(side="top", tickfont=dict(color="#94a3b8"), gridcolor="#1e293b"),
        yaxis=dict(
            title=dict(text="", font=dict(color="#94a3b8")),
            tickfont=dict(size=11, color="#cbd5e1"),
            autorange="reversed",
            gridcolor="#1e293b",
        ),
    )
    return fig


def _americas_altitude_scatter_figure(
    keep: pd.DataFrame,
    *,
    y_column: str,
    y_title: str,
) -> object | None:
    import plotly.graph_objects as go

    from app.plotly_theme import plotly_layout_base

    need = ["country_of_origin", "median_altitude", "lots", y_column]
    if any(c not in keep.columns for c in need):
        return None
    plot_df = keep.dropna(subset=["median_altitude", y_column]).copy()
    if plot_df.shape[0] < 2:
        return None

    sizes = (plot_df["lots"].astype(float).clip(lower=4) ** 0.55 * 5.5).clip(10, 36)
    fig = go.Figure(
        data=go.Scatter(
            x=plot_df["median_altitude"],
            y=plot_df[y_column],
            mode="markers",
            marker=dict(
                size=sizes,
                color="#e86f51",
                line=dict(width=1, color="#fca98a"),
                opacity=0.92,
            ),
            customdata=np.stack(
                [plot_df["country_of_origin"].astype(str), plot_df["lots"].astype(int)],
                axis=1,
            ),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Lots in sample: %{customdata[1]}<br>"
                "Median altitude: %{x:.0f} m<br>"
                f"{y_title}: %{{y:.2f}}<extra></extra>"
            ),
        )
    )
    _lay = plotly_layout_base(height=272)
    _m = dict(_lay["margin"])
    _m.update({"l": 54, "r": 22, "t": 46, "b": 42})
    _lay["margin"] = _m
    fig.update_layout(
        **_lay,
        title=dict(
            text=f"Median lot altitude vs {y_title.lower()}",
            font=dict(size=11, color="#cbd5e1"),
        ),
        xaxis=dict(
            title=dict(text="Median lot altitude (m)", font=dict(color="#94a3b8")),
            gridcolor="#1e293b",
            zeroline=False,
        ),
        yaxis=dict(
            title=dict(text=y_title, font=dict(color="#94a3b8")),
            gridcolor="#1e293b",
            zeroline=False,
        ),
    )
    return fig


def render() -> None:
    inject_page_theme_variant("americas")
    inject_region_page_css()
    st.markdown(
        """
<style>
  .s2-bridge.americas-map-bridge { padding: 0.72rem 0.95rem !important; margin: 0.45rem 0 1.2rem 0 !important; }
  .americas-step-spacer { height: 0.65rem; }
  .americas-step-spacer--sm { height: 0.38rem !important; }
  .americas-trade-interpret { margin-top: 0.42rem; }
  .americas-trade-interpret p {
    margin: 0 0 0.5rem 0;
    color: #c5cad3;
    font-size: 0.97rem;
    line-height: 1.55;
  }
  .americas-trade-interpret p:last-child { margin-bottom: 0; }
  .americas-terrain-stats { margin-top: 0.05rem !important; margin-bottom: 0.25rem !important; }
  .americas-terrain-stats p { margin: 0 !important; }
  .americas-terrain-foot { margin-top: 0.12rem !important; margin-bottom: 0.35rem !important; }
  .americas-terrain-foot p { margin: 0 !important; color: #c5cad3; font-size: 0.97rem; line-height: 1.55; }
  .americas-elev-subhd { font-weight: 600; color: #e8ecf1; font-size: 1.02rem; margin: 0.1rem 0 0.28rem 0; }
  .americas-elev-explain { color: #c5cad3; font-size: 0.96rem; line-height: 1.52; margin: 0 0 0.42rem 0; }
  .americas-elev-explain p { margin: 0 !important; }
  .americas-flavor-deemph { margin-bottom: 0.42rem !important; }
  .americas-flavor-deemph p { margin: 0 0 0.45rem 0 !important; font-size: 0.96rem !important; line-height: 1.52 !important; color: #c5cad3 !important; }
  .americas-heatmap-lead { margin: 0 0 0.2rem 0 !important; }
  .americas-heatmap-lead p { margin: 0 !important; font-size: 0.92rem !important; line-height: 1.48 !important; color: #aeb4bd !important; }
  .americas-soft-sep { height: 1px; background: rgba(255,255,255,0.07); margin: 0.48rem 0 0.52rem 0; }
  .americas-scatter-tight { margin: 0.05rem 0 0.12rem 0 !important; }
  .americas-scatter-tight p { margin: 0 !important; }
  .americas-divider-before-synth {
    height: 1px;
    background: rgba(255,255,255,0.08);
    margin: 1.35rem 0 1.55rem 0;
  }
  .americas-synth-title {
    font-size: 1.2rem;
    font-weight: 600;
    margin: 0.15rem 0 0.48rem 0 !important;
    color: #eef1f5;
  }
  .americas-synthesis-outro { margin-bottom: 0.15rem !important; }
  .americas-synthesis-outro p { margin: 0 !important; color: #c5cad3; font-size: 0.98rem; line-height: 1.58; }
  .americas-synthesis-outro p + p { margin-top: 0.75rem !important; }
  .americas-elev-explain p + p { margin-top: 0.45rem !important; }
  section[data-testid="stMain"] .block-container { padding-bottom: 1.15rem !important; }
</style>
        """,
        unsafe_allow_html=True,
    )
    sidebar_chapters("Americas")

    region_hero(
        "Americas",
        kicker="Where scale meets names you already know",
        title_override="Americas",
        lede=(
            "Brazil sets the volume story; Colombia and a belt of Central American and Andean names are already familiar on U.S. "
            "shelves and menus. Production scale, export visibility, broken highland geography, and how people talk about the cup "
            "line up more neatly here than in the other regional chapters. That alignment is why the Americas work as the cleanest "
            "first test of how far origin labels really carry."
        ),
    )

    # 1) Bridge from the landing map (Americas-only; no Compare/Conclusion tour)
    st.markdown(AMERICAS_MAP_BRIDGE_HTML, unsafe_allow_html=True)

    cup = rd.load_coffee_features()
    americas_cup = rd.coffee_features_for_region(cup, "Americas")
    prod = rd.production_for_region("Americas")
    imp = rd.imports_for_region("Americas")
    elev_ctx = rd.elevation_context_for_region("Americas")

    # 2) Why this region matters
    section_title("Why this region matters")
    st.markdown(
        """
The Americas are the natural first case study because familiar household names sit on **real tonnage** here. Brazil moves
industrial-scale volume; Colombia and neighbors stay visible on bags, menus, and cupping flights. Trade weight, upland geography,
and everyday recognition reinforce each other more cleanly than elsewhere.

That legibility is useful—and risky. When a shelf story looks this clear, it is easy to confuse recognition with precision.
The rest of the page tracks how much survives once you leave the label for the land, then the cup.
        """
    )

    section_divider()

    # 3) Trade and U.S. market context
    section_title("Trade and the U.S. market")
    st.markdown(
        """
This is the structural half of the chapter: the Americas are **heavy in the ledger**, not only easy to recognize on a menu.
The two bars put the same names under two lenses—**who grows the most** (left) and **who carries the largest U.S.-linked import values**
(right)—before the conversation turns to flavor. They show **structural weight**, not sensory proof.
        """
    )

    _prod_yr = rd.stage1_production_reference_year()
    _prod_yr_s = str(_prod_yr) if _prod_yr is not None else "latest year"
    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.markdown(
            f'<p class="s2-muted"><strong>Production by origin ({_prod_yr_s}, million tonnes)</strong></p>',
            unsafe_allow_html=True,
        )
        if not prod.empty and "production_tonnes_latest" in prod.columns:
            top_p = prod.nlargest(8, "production_tonnes_latest")[["country", "production_tonnes_latest"]].set_index(
                "country"
            )
            top_p["million_tonnes"] = top_p["production_tonnes_latest"] / 1_000_000.0
            st.bar_chart(top_p[["million_tonnes"]], height=248)
        else:
            st.info("Production table not available.")

    with c2:
        st.markdown(
            '<p class="s2-muted"><strong>U.S.-linked import value by origin</strong><br/>Nominal dollars, billions.</p>',
            unsafe_allow_html=True,
        )
        if not imp.empty and "import_value_or_quantity" in imp.columns:
            top_i = imp.nlargest(8, "import_value_or_quantity")[["country", "import_value_or_quantity"]].copy()
            top_i["billions"] = top_i["import_value_or_quantity"] / 1_000_000_000.0
            st.bar_chart(top_i.set_index("country")[["billions"]], height=248)
        else:
            st.info("Trade-by-origin file not available.")

    st.markdown(
        """
<div class="americas-trade-interpret">
  <p>
    <strong>Brazil</strong> still owns the production column; with <strong>Colombia</strong> it anchors most of the visible import-value signal here.
    Central America and the Andes sit a rung below without vanishing—a durable second tier on bags, menus, and wholesale lists.
  </p>
  <p>
    Read the bars as <strong>who carries structural weight</strong>, not a portrait of every shipment through U.S. ports.
  </p>
</div>
        """,
        unsafe_allow_html=True,
    )

    section_divider()
    st.markdown('<div class="americas-step-spacer americas-step-spacer--sm" aria-hidden="true"></div>', unsafe_allow_html=True)

    # 4) Elevation and geography
    section_title("Elevation and geography")
    st.markdown(
        """
Trade shows which origins carry weight in the ledger; terrain shows where coffee can plausibly sit **inside** those same names.
Across the Americas, lots keep clustering in higher, broken ground—ridges, plateaus, interior corridors—not in the widest basins a country name can hide.

A country reads as one place on a bag; the land behind it rarely is.
        """
    )

    st.markdown('<div class="americas-step-spacer americas-step-spacer--sm" aria-hidden="true"></div>', unsafe_allow_html=True)
    etopo.render_regional_topography_explorer("Americas", compact_vertical=True)

    st.markdown('<div class="americas-step-spacer americas-step-spacer--sm" aria-hidden="true"></div>', unsafe_allow_html=True)
    st.markdown(
        '<p class="americas-elev-subhd">Elevation comparisons across Americas origins</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
<div class="americas-elev-explain">
<p><strong>Left:</strong> median and spread of lot altitudes in this cupping sample. <strong>Right:</strong> a coarse terrain index per country from the same elevation table.
They belong together, but they are not the same photograph: one tracks where sampled lots report altitude; the other sketches the wider ground those names sit on.</p>
<p>Same altitude language on two bags can still mean different land stories.</p>
</div>
        """,
        unsafe_allow_html=True,
    )

    g1, g2 = st.columns(2, gap="large")
    with g1:
        st.markdown(
            '<p class="s2-muted"><strong>Lot altitude by origin</strong><br/>'
            "Cupping-sample lots: median, quartiles, and outliers.</p>",
            unsafe_allow_html=True,
        )
        alt_ctx = _country_altitude_context(americas_cup, elev_ctx)
        if alt_ctx.empty:
            st.caption("Not enough altitude data for country-level comparison.")
        else:
            order_candidates = alt_ctx.sort_values("lot_altitude_median", ascending=False)["country"].tolist()[:8]
            long_df = _lot_altitudes_long(americas_cup, order_candidates)
            if long_df.empty:
                st.caption("Not enough altitude data for country-level comparison.")
            else:
                counts = long_df.groupby("country").size()
                order = [c for c in order_candidates if int(counts.get(c, 0)) >= 5]
                long_df = long_df[long_df["country"].isin(order)]
                if len(order) >= 2 and not long_df.empty:
                    import plotly.graph_objects as go

                    from app.plotly_theme import PLOTLY_CONFIG, plotly_layout_base

                    fig_box = go.Figure()
                    for c in order:
                        vals = long_df.loc[long_df["country"] == c, "altitude"].astype(float)
                        fig_box.add_trace(
                            go.Box(
                                y=vals,
                                name=c,
                                boxpoints="suspectedoutliers",
                                marker_color="#e86f51",
                                line_color="#e86f51",
                                fillcolor="rgba(232,111,81,0.12)",
                            )
                        )
                    fig_box.update_layout(
                        **plotly_layout_base(height=258),
                        title=dict(
                            text="Lot altitude spread by origin (m)",
                            font=dict(size=12, color="#e2e8f0"),
                        ),
                        xaxis=dict(
                            title=dict(text="", font=dict(color="#94a3b8")),
                            categoryorder="array",
                            categoryarray=order,
                            tickangle=-26,
                            gridcolor="#1e293b",
                        ),
                        yaxis=dict(
                            title=dict(text="Altitude (m)", font=dict(color="#94a3b8")),
                            gridcolor="#1e293b",
                            zeroline=False,
                        ),
                        showlegend=False,
                    )
                    st.plotly_chart(fig_box, use_container_width=True, key="americas_lot_alt_box", config=PLOTLY_CONFIG)
                else:
                    show = (
                        alt_ctx.sort_values("lot_altitude_median", ascending=False)
                        .set_index("country")[["lot_altitude_p25", "lot_altitude_median", "lot_altitude_p75"]]
                    )
                    st.bar_chart(show, height=258)
                    st.caption("Few lots per country in this slice—showing quartile bars instead of boxes.")

    with g2:
        st.markdown(
            '<p class="s2-muted"><strong>Country terrain index</strong><br/>'
            "Broad country terrain from the same elevation table.</p>",
            unsafe_allow_html=True,
        )
        if not elev_ctx.empty and "representative_elevation_m" in elev_ctx.columns:
            ec = elev_ctx.sort_values("representative_elevation_m", ascending=False)
            st.bar_chart(ec.set_index("country")[["representative_elevation_m"]], height=258)
        else:
            st.caption("No country-level elevation context available.")

    section_divider()

    # 5) Flavor and cup profile
    st.markdown('<div class="americas-step-spacer americas-step-spacer--sm" aria-hidden="true"></div>', unsafe_allow_html=True)
    section_title("Flavor and cup profile")
    st.markdown(
        """
<div class="americas-flavor-deemph s2-section">
<p>There is no single “Americas flavor.” What shows up here is a <strong>related family</strong>: modest spread, some origins a bit brighter and more acid-forward,
others rounder and more body-forward. Country averages sketch broad tendencies in how this slice reaches U.S. specialty language. They do not lock any one bag or farm into a fixed personality.</p>
</div>
        """,
        unsafe_allow_html=True,
    )

    flavor = _country_flavor_summary(americas_cup)
    if not flavor.empty:
        from app.plotly_theme import PLOTLY_CONFIG

        keep = flavor[flavor["lots"] >= 4].head(8).copy()

        # Row 1: sensory heatmap (full width)
        st.markdown(
            '<div class="americas-heatmap-lead s2-muted"><p><strong>What changes across origins</strong><br/>'
            "Rows are countries; columns are mean traits on the usual cupping scale. Color is distance from the Americas average in this slice. "
            "Read the spread: once the rows sit side by side, the gaps stay small.</p></div>",
            unsafe_allow_html=True,
        )
        fig_hm = _americas_sensory_heatmap_figure(keep)
        if fig_hm is not None:
            st.plotly_chart(fig_hm, use_container_width=True, key="americas_sensory_heatmap", config=PLOTLY_CONFIG)
        else:
            st.caption("Not enough overlapping sensory columns to build a country comparison heatmap.")

        st.markdown('<div class="americas-soft-sep" aria-hidden="true"></div>', unsafe_allow_html=True)

        # Row 2: altitude scatter (full width)
        st.markdown(
            '<div class="americas-scatter-tight s2-muted"><p><strong>Altitude against one trait</strong><br/>'
            "Each point is a country; marker size reflects lot count. Exploratory only—pick a vertical axis and watch how median lot altitude drifts with part of the profile.</p></div>",
            unsafe_allow_html=True,
        )
        scatter_specs: list[tuple[str, str, str]] = [
            ("Mean acidity", "acidity", "Mean acidity"),
            ("Mean body", "body", "Mean body"),
            ("Mean flavor", "flavor", "Mean flavor"),
            ("Mean balance", "balance", "Mean balance"),
            ("Mean overall", "overall", "Mean overall"),
            ("Mean total cup points", "mean_total_points", "Mean total cup points"),
        ]
        options = [(lab, col, title) for lab, col, title in scatter_specs if col in keep.columns]
        if keep.dropna(subset=["median_altitude"]).empty or len(options) == 0:
            st.caption("Insufficient altitude or sensory columns for this comparison.")
        else:
            labels = [o[0] for o in options]
            default_i = next((i for i, o in enumerate(options) if o[1] == "acidity"), 0)
            pick = st.selectbox(
                "Compare altitude with:",
                options=labels,
                index=min(default_i, len(labels) - 1),
                key="americas_altitude_scatter_y",
            )
            _, y_col, y_title = options[labels.index(pick)]
            fig_sc = _americas_altitude_scatter_figure(keep, y_column=y_col, y_title=y_title)
            if fig_sc is not None:
                st.plotly_chart(
                    fig_sc, use_container_width=True, key="americas_altitude_scatter", config=PLOTLY_CONFIG
                )
            else:
                st.caption("Need at least two countries with both median altitude and the chosen metric.")

        st.markdown(
            """
A loose pattern, not a law: higher median altitudes here often read a touch brighter and more acid-forward; rounder profiles can carry a bit more body and balance.
The gaps are **real** and still **narrower than bag copy often claims**. Variety, processing, and which lots enter the sample still steer the cup.
            """
        )
    else:
        st.info("No sensory aggregates available for the Americas slice.")

    st.markdown('<div class="americas-divider-before-synth" aria-hidden="true"></div>', unsafe_allow_html=True)

    # 6) Closing interpretation
    st.markdown(
        '<div class="americas-synth-title">What the Americas contribute</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
<div class="americas-synthesis-outro s2-section">
<p>The Americas anchor much of what U.S. drinkers meet in the cup: trade volume and everyday recognition really do reinforce each other here.
<strong>Brazil</strong> carries structural scale; <strong>Colombia</strong> and <strong>Central America</strong> add continuity and outsized specialty visibility relative to their tonnage.
On the land, the signal keeps bending toward upland belts, not anonymous lowland averages.</p>
<p>Even here, the cup does not resolve into one neat regional character. Where scale, broken terrain, and familiarity line up as cleanly as anywhere in the project, the sensory read is still a <strong>structured mix</strong>: family resemblance, not a single verdict.
Labels carry <strong>real context</strong> without carrying <strong>total certainty</strong>. If the clearest case stays this blended, “single origin” probably deserves a slower read than the shelf usually encourages.</p>
</div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div style="margin:0;padding:0;height:0;line-height:0;font-size:0;margin-top:-0.28rem" aria-hidden="true"></div>',
        unsafe_allow_html=True,
    )

    chapter_footer_full_arc()
