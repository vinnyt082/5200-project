"""Regional chapters for Africa and Asia-Pacific (Americas-parallel layout)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from app.stage2 import elevation_topography as etopo
from app.stage2 import region_data as rd
from app.stage2.region_shell import (
    REGION_META,
    chapter_footer_full_arc,
    inject_page_theme_variant,
    inject_region_page_css,
    map_bridge,
    region_hero,
    section_divider,
    section_title,
    sidebar_chapters,
)


REGION_OPENING = {
    "Africa": (
        "Many American drinkers first meet <em>Ethiopia</em>, <em>Kenya</em>, and <em>Uganda</em> as mountain-grown names—"
        "brightness, clarity, altitude, distinction—before anything reads like a spreadsheet row. In American coffee talk, "
        "Africa often arrives half-mythologized. What follows traces those names through concentrated trade and broken terrain, "
        "then asks what the cup averages in this sample actually support."
    ),
    "Asia-Pacific": (
        "<strong>Vietnam</strong> supplies scale; <strong>Indonesia</strong> adds island highlands; smaller origins keep "
        "distinctive elevated threads alive. Asia-Pacific may be the <strong>widest internal spread</strong> in these pages: "
        "bulk systems, volcanic arcs, island uplands, and smaller names under one shelf label—not one production story. "
        "What follows tracks that spread through trade, terrain, and what the cup averages in this sample actually preserve."
    ),
}


AFRICA_MAP_BRIDGE_HTML = """
<div class="s2-bridge africa-map-bridge">
  <p>The home map situates African origins in the U.S. import frame. Here those names widen: where value concentrates,
  how the land reads, and how much of the familiar story still shows in the sample cups.</p>
</div>
"""


ASIA_PACIFIC_BRIDGE_HTML = """
<div class="s2-bridge apac-map-bridge">
  <p>The home map situates Asia-Pacific in the U.S. import frame. Here those names open up: who anchors scale, where coffee
  clusters in the landscape, and how unevenly those differences carry into the cup.</p>
</div>
"""


def _country_altitude_context(region_cup: pd.DataFrame, elev_ctx: pd.DataFrame) -> pd.DataFrame:
    cup = (
        region_cup.dropna(subset=["country_of_origin", "altitude"])
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


def _lot_altitudes_long(region_cup: pd.DataFrame, countries: list[str]) -> pd.DataFrame:
    """Per-lot altitudes for elevation box plots (same pattern as Americas; avoids duplicate ``country`` cols)."""
    cup = region_cup.dropna(subset=["country_of_origin", "altitude"])
    if cup.empty or not countries:
        return pd.DataFrame(columns=["country", "altitude"])
    cup = cup[cup["country_of_origin"].isin(countries)]
    out = cup[["country_of_origin", "altitude"]].copy()
    return out.rename(columns={"country_of_origin": "country"})


def _country_flavor_summary(region_cup: pd.DataFrame) -> pd.DataFrame:
    """Per-country means for cup profile views (lot-level sample; columns included when present)."""
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
    sub = region_cup.dropna(subset=["country_of_origin"])
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


def _sensory_heatmap_figure(
    keep: pd.DataFrame,
    *,
    slice_label: str,
    warm_color: str,
    figure_title: str,
) -> object | None:
    """Country × sensory heatmap; color = deviation from slice mean (same logic as Americas page)."""
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
            textfont={"size": 11, "color": "#e8ecf1"},
            colorscale=[
                [0.0, "#4a6fa5"],
                [0.5, "#1e293b"],
                [1.0, warm_color],
            ],
            zmid=0.0,
            zmin=-vmax,
            zmax=vmax,
            hovertemplate=(
                "<b>%{y}</b> · %{x}<br>"
                "Mean (this slice): %{text:.2f}<br>"
                f"Δ vs {slice_label} mean: %{{z:+.2f}}<extra></extra>"
            ),
            colorbar=dict(
                title=dict(text=f"Δ vs<br>{slice_label} mean", font=dict(size=10, color="#94a3b8")),
                tickfont=dict(color="#94a3b8"),
            ),
        )
    )
    row_h = max(44, min(52, 360 // max(raw.shape[0], 1)))
    fig.update_layout(
        **plotly_layout_base(height=80 + row_h * raw.shape[0]),
        title=dict(text=figure_title, font=dict(size=12, color="#e2e8f0")),
        xaxis=dict(side="top", tickfont=dict(color="#94a3b8"), gridcolor="#1e293b"),
        yaxis=dict(
            title=dict(text="", font=dict(color="#94a3b8")),
            tickfont=dict(size=11, color="#cbd5e1"),
            autorange="reversed",
            gridcolor="#1e293b",
        ),
    )
    return fig


def _altitude_trait_scatter_figure(
    keep: pd.DataFrame,
    *,
    y_column: str,
    y_title: str,
    marker_color: str,
    line_color: str,
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
                color=marker_color,
                line=dict(width=1, color=line_color),
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
    fig.update_layout(
        **plotly_layout_base(height=320),
        title=dict(
            text=f"Median lot altitude vs {y_title.lower()}",
            font=dict(size=12, color="#e2e8f0"),
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


def _trade_interp(region_key: str) -> str:
    if region_key == "Africa":
        return """<div class="africa-trade-interpret"><p>
In this slice, <strong>Ethiopia</strong> and <strong>Uganda</strong> carry most of the visible import weight, while
<strong>Kenya</strong> can look modest on the bars and still stay instantly legible in café and tasting-note language.
<strong>The ledger reads narrow; the reputation reads wider</strong>—that is the structural tension this page keeps in view.
</p><p>
Use the spacing to read concentration, not as a full customs census.
</p></div>"""
    if region_key == "Asia-Pacific":
        return """<div class="apac-trade-interpret"><p>
<strong>Vietnam</strong> and <strong>Indonesia</strong> anchor production and import heft in this slice, but the silhouette stays plural.
<strong>Thailand</strong>, <strong>Laos</strong>, <strong>Taiwan</strong>, and other smaller names still matter less for sheer tonnes than for the
<strong>different market and terrain identities</strong> they keep visible in the region.
</p><p>
Read the bars for <strong>relative structure</strong>, not as a customs tally.
</p></div>"""
    return (
        "**Vietnam** and **Indonesia** dominate the scale picture here, but the region is **not** a one-country story. "
        "Smaller origins in this slice—**Thailand**, **Laos**, **Taiwan**, and others where they appear—matter less "
        "for sheer tonnage than for the **different terrain and market roles** they represent. The takeaway is "
        "**contrast inside one label**, not a flat ranking of winners and losers; read the bars for **relative "
        "structure**, not as a full customs accounting."
    )


def _takeaway(region_key: str) -> str:
    return (
        "Asia-Pacific contributes both backbone and range: large-scale supply from Vietnam and "
        "Indonesia alongside smaller highland-origin stories across Southeast Asia and the Pacific. "
        "Terrain and elevation patterns span volcanic islands, interior uplands, and plateau systems, "
        "which helps explain why market identity here runs from dependable blend structure to "
        "distinctive single-origin profiles."
    )


def render(region_key: str) -> None:
    variant = (
        "africa"
        if region_key == "Africa"
        else "asia-pacific"
        if region_key == "Asia-Pacific"
        else "americas"
    )
    inject_page_theme_variant(variant)
    meta = REGION_META[region_key]
    inject_region_page_css()
    if region_key in ("Africa", "Asia-Pacific"):
        st.markdown(
            """
<style>
  .s2-bridge.africa-map-bridge,
  .s2-bridge.apac-map-bridge { padding: 0.72rem 0.95rem !important; margin: 0.45rem 0 1.2rem 0 !important; }
  .africa-step-spacer,
  .apac-step-spacer { height: 0.65rem; }
  .africa-trade-interpret p,
  .apac-trade-interpret p {
    margin: 0 0 0.45rem 0;
    color: #c5cad3;
    font-size: 0.98rem;
    line-height: 1.58;
  }
  .africa-trade-interpret p:last-child,
  .apac-trade-interpret p:last-child { margin-bottom: 0; }
  .africa-trade-interpret { margin-top: 0.35rem; }
  .apac-trade-interpret { margin-top: 0.35rem; }
</style>
            """,
            unsafe_allow_html=True,
        )
    sidebar_chapters(region_key)
    hero_kicker = (
        "Highland history, concentrated trade"
        if region_key == "Africa"
        else "Volume anchors, islands, and niches"
        if region_key == "Asia-Pacific"
        else "Regional case study"
    )
    region_hero(
        region_key,
        kicker=hero_kicker,
        title_override=meta["title"],
        lede=REGION_OPENING.get(region_key, ""),
    )
    if region_key == "Africa":
        st.markdown(AFRICA_MAP_BRIDGE_HTML, unsafe_allow_html=True)
    elif region_key == "Asia-Pacific":
        st.markdown(ASIA_PACIFIC_BRIDGE_HTML, unsafe_allow_html=True)
    else:
        map_bridge()

    cup = rd.load_coffee_features()
    region_cup = rd.coffee_features_for_region(cup, region_key)
    prod = rd.production_for_region(region_key)
    imp = rd.imports_for_region(region_key)
    elev_ctx = rd.elevation_context_for_region(region_key)

    section_title("Why this region matters")
    if region_key == "Africa":
        st.markdown(
            """
Africa is especially revealing because **café language often runs ahead of simple tonnage**. Menus and tasting notes lean on
upland romance—brightness, florality, elegance, origin distinction—while the spreadsheets stay comparatively tight. That mismatch
is the useful part: it asks, in unusually clear form, how trade weight, mountain geography, and sensory reputation do—and do
not—move together.

If the Americas put labels most obviously on scale, Africa is where **names travel farther than scale alone would suggest**.
That does not make the story false; it makes it worth reading slowly.
            """
        )
    elif region_key == "Asia-Pacific":
        st.markdown(
            """
The Asia-Pacific label is useful precisely because it **bundles systems that rarely move in lockstep**. A few origins carry
very large volume; others stay visible through smaller markets, distinctive terrain, or the way coffees are talked about—more
than raw tonnage alone would predict. That makes the region a clean stress test: **scale, geography, and sensory identity pull apart here more than the label suggests**.

If the Americas show labels sitting on obvious mass, and Africa shows **reputation outrunning tonnage**, Asia-Pacific shows something else:
**one name covering several market roles at once**.
            """
        )
    else:
        st.markdown(
            f"""
{meta["title"]} sits at a critical intersection of volume, geography, and cup identity. The same
origin labels that appear in U.S. retail and café contexts map to very different landscapes inside
this region, from lower-elevation production belts to highland systems that dominate quality narratives.
            """
        )

    section_divider()
    if region_key == "Africa":
        st.markdown('<div class="africa-step-spacer" aria-hidden="true"></div>', unsafe_allow_html=True)
    elif region_key == "Asia-Pacific":
        st.markdown('<div class="apac-step-spacer" aria-hidden="true"></div>', unsafe_allow_html=True)
    section_title("Trade and the U.S. market")
    if region_key == "Africa":
        st.markdown(
            """
The Africa bars read deliberately tight: a few origins carry most of the import signal, and a sparse right-hand chart still
says **concentration**, not absence. Here a quiet bar can sit next to a **loud name** in how Americans talk about coffee.
**Trade weight is part of the story, not the whole cultural footprint**—market weight and imaginative weight visibly separate.
            """
        )
    elif region_key == "Asia-Pacific":
        st.markdown(
            """
Structural read, side by side: **who grows at scale** versus **who registers in U.S.-linked import value**. The picture is
top-heavy—**Vietnam** and **Indonesia** carry most of the visible mass—yet it does not collapse into two names. Smaller rows
still matter because they carry **different terrain stories and market roles** that tonnage alone does not capture.
            """
        )
    else:
        st.markdown(
            """
As in the Americas chapter, these charts focus on relative structure: production scale at left and
U.S.-linked import value at right.
            """
        )

    _ref_yr = rd.stage1_production_reference_year()
    _ref_yr_s = str(_ref_yr) if _ref_yr is not None else "latest year"
    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.markdown(
            f'<p class="s2-muted"><strong>Production by origin ({_ref_yr_s}, million tonnes)</strong></p>',
            unsafe_allow_html=True,
        )
        if not prod.empty and "production_tonnes_latest" in prod.columns:
            top_p = prod.nlargest(8, "production_tonnes_latest")[["country", "production_tonnes_latest"]].set_index(
                "country"
            )
            top_p["million_tonnes"] = top_p["production_tonnes_latest"] / 1_000_000.0
            st.bar_chart(top_p[["million_tonnes"]], height=290)
        else:
            st.info("Production table not available.")

    with c2:
        st.markdown(
            '<p class="s2-muted"><strong>U.S.-linked import value (nominal dollars, billions)</strong><br/>'
            "Top origins in this view.</p>",
            unsafe_allow_html=True,
        )
        if not imp.empty and "import_value_or_quantity" in imp.columns:
            top_i = imp.nlargest(8, "import_value_or_quantity")[["country", "import_value_or_quantity"]].copy()
            top_i["billions"] = top_i["import_value_or_quantity"] / 1_000_000_000.0
            st.bar_chart(top_i.set_index("country")[["billions"]], height=290)
        else:
            st.info("Trade-by-origin file not available.")

    if region_key == "Africa":
        st.markdown('<div class="africa-step-spacer" aria-hidden="true"></div>', unsafe_allow_html=True)
    elif region_key == "Asia-Pacific":
        st.markdown('<div class="apac-step-spacer" aria-hidden="true"></div>', unsafe_allow_html=True)
    st.markdown(_trade_interp(region_key), unsafe_allow_html=(region_key in ("Africa", "Asia-Pacific")))

    section_divider()
    if region_key == "Africa":
        st.markdown('<div class="africa-step-spacer" aria-hidden="true"></div>', unsafe_allow_html=True)
    elif region_key == "Asia-Pacific":
        st.markdown('<div class="apac-step-spacer" aria-hidden="true"></div>', unsafe_allow_html=True)
    section_title("Elevation and geography")
    if region_key == "Africa":
        st.markdown(
            """
Trade marks which African origins carry export weight; terrain shows where coffee can plausibly sit **inside** those borders.
“Africa” still wraps very different landscapes—escarpments, plateaus, upland pockets, broader belts—so this chapter works
better as **a set of countries** than as one uniform elevation story.
            """
        )
    elif region_key == "Asia-Pacific":
        st.markdown(
            """
Trade shows which Asia-Pacific names carry market weight; terrain shows where coffee can plausibly sit inside them. Coasts,
volcanic belts, uplands, interior pockets, and plains nest tightly here, so a regional—or even national—label can
**smooth over an unusually fragmented landscape**.
            """
        )
    else:
        st.markdown(
            """
Market shares show where coffee enters trade; terrain helps explain where coffee is plausibly grown
inside each origin. The map and support charts pair those two views.
            """
        )

    if region_key == "Africa":
        st.markdown('<div class="africa-step-spacer" aria-hidden="true"></div>', unsafe_allow_html=True)
    elif region_key == "Asia-Pacific":
        st.markdown('<div class="apac-step-spacer" aria-hidden="true"></div>', unsafe_allow_html=True)
    etopo.render_regional_topography_explorer(region_key)

    if region_key == "Africa":
        st.markdown('<div class="africa-step-spacer" aria-hidden="true"></div>', unsafe_allow_html=True)
        st.markdown("**Elevation comparisons across Africa origins**")
        st.markdown(
            """
**Left:** lot altitudes reported in this sample. **Right:** a coarse national terrain index from the same elevation table.
The two are **related, not identical**: one tracks where sampled cups say they grew; the other tracks the broader land behind those names.

That gap matters here because **mountain-coded language** sells on labels more cleanly than national relief behaves on the ground.
            """
        )
    elif region_key == "Asia-Pacific":
        st.markdown('<div class="apac-step-spacer" aria-hidden="true"></div>', unsafe_allow_html=True)
        st.markdown("**Elevation comparisons across Asia-Pacific origins**")
        st.markdown(
            """
**Left:** reported lot altitudes in this cupping sample. **Right:** a coarse national terrain index from the same elevation table.
The two are **related, not identical**. In this region, bulk production, island relief, and interior belts do not collapse into one tidy elevation story.

That is why these averages need **country context** more than shorthand.
            """
        )
    else:
        st.markdown(f"**Elevation comparisons across {meta['title']} origins**")
        st.markdown(
            """
The first chart summarizes lot-altitude spread in this dataset; the second provides broader country
elevation context. Together they make cross-country elevation patterns easier to compare.
            """
        )

    g1, g2 = st.columns(2, gap="large")
    with g1:
        if region_key == "Africa":
            st.markdown(
                '<p class="s2-muted"><strong>Lot altitude by origin</strong><br/>'
                "Cupping-sample lots: median, quartiles, and outliers.</p>",
                unsafe_allow_html=True,
            )
            import plotly.graph_objects as go

            from app.plotly_theme import PLOTLY_CONFIG, plotly_layout_base

            alt_ctx = _country_altitude_context(region_cup, elev_ctx)
            if alt_ctx.empty:
                st.caption("Not enough altitude data for country-level comparison.")
            else:
                order_candidates = alt_ctx.sort_values("lot_altitude_median", ascending=False)["country"].tolist()[:8]
                long_df = _lot_altitudes_long(region_cup, order_candidates)
                if long_df.empty:
                    st.caption("Not enough altitude data for country-level comparison.")
                else:
                    counts = long_df.groupby("country").size()
                    order = [c for c in order_candidates if int(counts.get(c, 0)) >= 5]
                    long_df = long_df[long_df["country"].isin(order)]
                    if len(order) >= 2 and not long_df.empty:
                        accent = meta.get("accent", "#58c486")
                        fig_box = go.Figure()
                        for c in order:
                            vals = long_df.loc[long_df["country"] == c, "altitude"].astype(float)
                            fig_box.add_trace(
                                go.Box(
                                    y=vals,
                                    name=c,
                                    boxpoints="suspectedoutliers",
                                    marker_color=accent,
                                    line_color=accent,
                                    fillcolor="rgba(88, 196, 134, 0.12)",
                                )
                            )
                        fig_box.update_layout(
                            **plotly_layout_base(height=280),
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
                        st.plotly_chart(
                            fig_box, use_container_width=True, key="africa_lot_alt_box", config=PLOTLY_CONFIG
                        )
                    else:
                        show = (
                            alt_ctx.sort_values("lot_altitude_median", ascending=False)
                            .set_index("country")[["lot_altitude_p25", "lot_altitude_median", "lot_altitude_p75"]]
                        )
                        st.bar_chart(show, height=280)
                        st.caption("Few lots per country in this slice—showing quartile bars instead of boxes.")
        elif region_key == "Asia-Pacific":
            st.markdown(
                '<p class="s2-muted"><strong>Lot altitude by origin</strong><br/>'
                "Cupping-sample lots: median, quartiles, and outliers.</p>",
                unsafe_allow_html=True,
            )
            import plotly.graph_objects as go

            from app.plotly_theme import PLOTLY_CONFIG, plotly_layout_base

            alt_ctx = _country_altitude_context(region_cup, elev_ctx)
            if alt_ctx.empty:
                st.caption("Not enough altitude data for country-level comparison.")
            else:
                order_candidates = alt_ctx.sort_values("lot_altitude_median", ascending=False)["country"].tolist()[:8]
                long_df = _lot_altitudes_long(region_cup, order_candidates)
                if long_df.empty:
                    st.caption("Not enough altitude data for country-level comparison.")
                else:
                    counts = long_df.groupby("country").size()
                    order = [c for c in order_candidates if int(counts.get(c, 0)) >= 5]
                    long_df = long_df[long_df["country"].isin(order)]
                    if len(order) >= 2 and not long_df.empty:
                        accent = meta.get("accent", "#68a2ff")
                        fig_box = go.Figure()
                        for c in order:
                            vals = long_df.loc[long_df["country"] == c, "altitude"].astype(float)
                            fig_box.add_trace(
                                go.Box(
                                    y=vals,
                                    name=c,
                                    boxpoints="suspectedoutliers",
                                    marker_color=accent,
                                    line_color=accent,
                                    fillcolor="rgba(104, 162, 255, 0.12)",
                                )
                            )
                        fig_box.update_layout(
                            **plotly_layout_base(height=280),
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
                        st.plotly_chart(
                            fig_box, use_container_width=True, key="apac_lot_alt_box", config=PLOTLY_CONFIG
                        )
                    else:
                        show = (
                            alt_ctx.sort_values("lot_altitude_median", ascending=False)
                            .set_index("country")[["lot_altitude_p25", "lot_altitude_median", "lot_altitude_p75"]]
                        )
                        st.bar_chart(show, height=280)
                        st.caption("Few lots per country in this slice—showing quartile bars instead of boxes.")
        else:
            st.markdown(
                '<p class="s2-muted">Lot altitude distribution by country (IQR and median)</p>',
                unsafe_allow_html=True,
            )
            alt_ctx = _country_altitude_context(region_cup, elev_ctx)
            if not alt_ctx.empty:
                show = (
                    alt_ctx.sort_values("lot_altitude_median", ascending=False)
                    .set_index("country")[["lot_altitude_p25", "lot_altitude_median", "lot_altitude_p75"]]
                )
                st.bar_chart(show, height=280)
            else:
                st.caption("Not enough altitude data for country-level comparison.")

    with g2:
        if region_key == "Africa":
            st.markdown(
                '<p class="s2-muted"><strong>Country terrain context</strong><br/>'
                "Coarse national relief—pair with lot altitude to see how country-scale terrain relates to where sampled cups "
                "report they were grown.</p>",
                unsafe_allow_html=True,
            )
        elif region_key == "Asia-Pacific":
            st.markdown(
                '<p class="s2-muted"><strong>Country terrain context</strong><br/>'
                "Coarse national relief—pair with lot altitude when islands and interior belts do not tell one simple elevation story.</p>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<p class="s2-muted">Country representative elevation context</p>',
                unsafe_allow_html=True,
            )
        if not elev_ctx.empty and "representative_elevation_m" in elev_ctx.columns:
            ec = elev_ctx.sort_values("representative_elevation_m", ascending=False)
            st.bar_chart(ec.set_index("country")[["representative_elevation_m"]], height=280)
        else:
            st.caption("No country-level elevation context available.")

    section_divider()
    if region_key == "Africa":
        st.markdown('<div class="africa-step-spacer" aria-hidden="true"></div>', unsafe_allow_html=True)
    elif region_key == "Asia-Pacific":
        st.markdown('<div class="apac-step-spacer" aria-hidden="true"></div>', unsafe_allow_html=True)
    section_title("Flavor and cup profile")

    flavor = _country_flavor_summary(region_cup)
    if region_key == "Africa":
        st.markdown(
            """
There is no single “Africa flavor.” What shows is a **recognizable family** tied to how Americans learn to talk about the region:
brightness, florality, clarity, mountain-coded distinction. Some country averages lean more lifted and acid-forward; others read
rounder. The useful read is **pattern with limits**, not **stereotype confirmed**—reputation from overlapping tendencies in this
slice, **not one flavor script for every bag**.
            """
        )
        if not flavor.empty:
            from app.plotly_theme import PLOTLY_CONFIG

            keep = flavor[flavor["lots"] >= 4].head(8).copy()

            st.markdown(
                '<p class="s2-muted"><strong>What separates the profiles</strong><br/>'
                "Rows are countries; columns are mean traits on the usual cupping scale. Color is distance from the Africa average "
                "in this slice. The read is not who “wins,” but how <strong>small and interpretable</strong> the gaps stay once the "
                "profiles sit side by side.</p>",
                unsafe_allow_html=True,
            )
            fig_hm = _sensory_heatmap_figure(
                keep,
                slice_label="Africa",
                warm_color=meta.get("accent", "#58c486"),
                figure_title="Mean traits by origin (color vs Africa average in this slice)",
            )
            if fig_hm is not None:
                st.plotly_chart(fig_hm, use_container_width=True, key="africa_sensory_heatmap", config=PLOTLY_CONFIG)
            else:
                st.caption("Not enough overlapping sensory columns to build a country comparison heatmap.")

            st.divider()

            st.markdown(
                '<p class="s2-muted"><strong>Altitude against one trait</strong><br/>'
                "Each point is a country; marker size reflects lot count behind the average. Exploratory only: median altitude and "
                "traits sometimes move together here, never cleanly enough to stand in for the whole story.</p>",
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
                    key="africa_altitude_scatter_y",
                )
                _, y_col, y_title = options[labels.index(pick)]
                fig_sc = _altitude_trait_scatter_figure(
                    keep,
                    y_column=y_col,
                    y_title=y_title,
                    marker_color=meta.get("accent", "#58c486"),
                    line_color="#7dd3ae",
                )
                if fig_sc is not None:
                    st.plotly_chart(
                        fig_sc, use_container_width=True, key="africa_altitude_scatter", config=PLOTLY_CONFIG
                    )
                else:
                    st.caption("Need at least two countries with both median altitude and the chosen metric.")

            st.markdown(
                """
Altitude and acidity or balance sometimes drift together in these country averages—higher medians a touch brighter—but that is
**not a rule**. Reputation here rests on **repeated tendencies** in language and on the table, not a universal profile; variety,
processing, and which lots enter the sample still steer the cup.
                """
            )
        else:
            st.info("No sensory aggregates available for the Africa slice.")
    elif region_key == "Asia-Pacific":
        st.markdown(
            """
There is no single Asia-Pacific cup signature in this sample. Some country averages read rounder, steadier, or more supply-oriented;
others lean more lifted, narrower, or more distinctive. The useful read is not forced unity; it is **how much range one regional label can hide** once the rows sit side by side.
            """
        )
        if not flavor.empty:
            from app.plotly_theme import PLOTLY_CONFIG

            keep = flavor[flavor["lots"] >= 4].head(8).copy()

            st.markdown(
                '<div class="apac-step-spacer" aria-hidden="true"></div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                '<p class="s2-muted"><strong>What separates the profiles</strong><br/>'
                "Rows are countries; columns are mean traits on the usual cupping scale. Color shows distance from the Asia-Pacific "
                "average in this slice. The key read is <strong>spread</strong>: this region resists one clean sensory script more than shelf labels suggest.</p>",
                unsafe_allow_html=True,
            )
            fig_hm = _sensory_heatmap_figure(
                keep,
                slice_label="Asia-Pacific",
                warm_color=meta.get("accent", "#68a2ff"),
                figure_title="Mean traits by origin (color vs Asia-Pacific average in this slice)",
            )
            if fig_hm is not None:
                st.plotly_chart(fig_hm, use_container_width=True, key="apac_sensory_heatmap", config=PLOTLY_CONFIG)
            else:
                st.caption("Not enough overlapping sensory columns to build a country comparison heatmap.")

            st.divider()

            st.markdown(
                '<p class="s2-muted"><strong>Altitude against one trait</strong><br/>'
                "Each point is a country; marker size reflects lot count behind the average. Treat this as "
                "<strong>exploratory context, not a formula</strong>: altitude and sensory traits rarely line up cleanly here because production system, "
                "variety, process, and market role still weigh in.</p>",
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
                    key="apac_altitude_scatter_y",
                )
                _, y_col, y_title = options[labels.index(pick)]
                fig_sc = _altitude_trait_scatter_figure(
                    keep,
                    y_column=y_col,
                    y_title=y_title,
                    marker_color=meta.get("accent", "#68a2ff"),
                    line_color="#96c8ff",
                )
                if fig_sc is not None:
                    st.plotly_chart(
                        fig_sc, use_container_width=True, key="apac_altitude_scatter", config=PLOTLY_CONFIG
                    )
                else:
                    st.caption("Need at least two countries with both median altitude and the chosen metric.")

            st.markdown(
                """
A loose tilt can appear when altitude meets brighter or more distinctive traits in these country averages, but it is **not a rule**.
Lower or larger-scale systems may read rounder or steadier; more elevated systems may read narrower or more distinctive.
Production system, processing, variety, and sample composition still steer the cup—think **parallel stories**, not one altitude equation per origin.
                """
            )
        else:
            st.info("No sensory aggregates available for the Asia-Pacific slice.")
    else:
        st.markdown(
            """
Core sensory averages by country and a simple altitude-versus-score view keep this section readable
while the region’s production and trade stories stay up-page.
            """
        )

        if not flavor.empty:
            keep = flavor[flavor["lots"] >= 3].head(8).copy()

            f1, f2 = st.columns(2, gap="large")
            with f1:
                st.markdown(
                    '<p class="s2-muted">Country flavor profile (mean acidity, flavor, body)</p>',
                    unsafe_allow_html=True,
                )
                profile = keep.set_index("country_of_origin")[["acidity", "flavor", "body"]]
                st.bar_chart(profile, height=310)

            with f2:
                st.markdown(
                    '<p class="s2-muted">Country median altitude vs. mean total cup points</p>',
                    unsafe_allow_html=True,
                )
                comp = keep.dropna(subset=["median_altitude", "mean_total_points"])
                if not comp.empty:
                    st.scatter_chart(
                        comp,
                        x="median_altitude",
                        y="mean_total_points",
                        color="country_of_origin",
                        size="lots",
                        height=310,
                    )
                else:
                    st.caption("Insufficient rows for country-level altitude/score comparison.")

            st.markdown(
                """
Patterns are suggestive rather than deterministic: higher-altitude country medians often align with
somewhat brighter or higher-scoring averages, but overlap is substantial and processing, variety,
and sample composition remain important.
                """
            )
        else:
            st.info(f"No sensory aggregates available for {meta['title']}.")

    section_divider()
    if region_key == "Africa":
        section_title("What Africa contributes")
        st.markdown(
            """
Africa contributes some of the **most legible origin identities** in the U.S. cup—names that travel farther in café and tasting-note
language than import rankings alone would predict. Broken upland terrain helps those stories stick, and some cup tendencies are
plain in the averages.

Trade concentration still does not carry the full cultural weight around brightness, florality, clarity, and distinction.
“African coffee” is not hollow: **the label works best as a cluster of expectations, not a guarantee**. That is not proof that
origin fails to matter—only that **the strongest origin stories are often the most compressed**, and the most vivid ones reward a slower read.
            """
        )
    elif region_key == "Asia-Pacific":
        section_title("What Asia-Pacific contributes")
        st.markdown(
            """
Asia-Pacific contributes both **backbone and range** to the U.S. cup. **Vietnam** and **Indonesia** anchor scale, while smaller
elevated and island-origin threads keep the region from collapsing into one supply story. Terrain helps explain that spread;
production systems and market roles complete the picture.

The point is not one regional flavor. It is **one of the widest spans of identity** in these pages—from steady, supply-oriented profiles to narrower, more distinctive cups.

If the Americas show familiarity and Africa shows compressed reputation, Asia-Pacific shows something else: **how much difference one tidy shelf label can quietly contain**. Regional names stay **useful containers**; they are **weak summaries** of what is inside.
            """
        )
    else:
        section_title("Regional takeaway")
        st.markdown(_takeaway(region_key))

    chapter_footer_full_arc()
