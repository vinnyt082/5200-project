from __future__ import annotations

from pathlib import Path

import pandas as pd
import pydeck as pdk
import streamlit as st

from app.config import (
    MAP_BACKUP_IMAGE_PATH,
    MAP_MODE,
    REGION_COLORS,
    US_COFFEE_IMPORTS_TIMESERIES_PATH,
    streamlit_page_icon,
)
from app.data_loader import load_stage1_data
from app.map_layers import build_map_layers, initial_view_state
from app.sidebar_theme import inject_sidebar_theme_css
from app.stage2.region_shell import (
    MAIN_CHAPTER_FOOTER_CSS,
    inject_page_theme_variant,
    render_chapter_footer_nav,
    render_chapter_nav_links,
)

# Map layer sizing only (marker fill color stays region-based in ``map_layers``).
_DEFAULT_MAP_METRIC = "Production"


def _load_timeseries_csv(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    df = pd.read_csv(path)
    if df.empty or "year" not in df.columns or "value" not in df.columns:
        return None
    df = df.sort_values("year").dropna(subset=["year", "value"])
    return df


def _imports_narrative(df: pd.DataFrame) -> str:
    """Short read of what the line shows: level and persistence, not year-by-year trivia."""
    y0, y1 = int(df["year"].min()), int(df["year"].max())
    if len(df) < 2 or float(df["value"].fillna(0).max()) <= 0:
        return "Too few points in this window to read a long-run arc."
    return (
        f"From {y0} through {y1}, the trace rides a high band. Shocks and seasons ripple the totals, "
        "but the country never really walks away from foreign supply. That steadiness is the point: imports "
        "sit near the center of how the American coffee market is built, not at the margin."
    )


def _plotly_landing_line(
    df: pd.DataFrame, *, title: str, y_title: str, y_tick_format: str
):
    """Interactive Plotly line (embedded figure, not a static PNG)."""
    import plotly.graph_objects as go

    from app.plotly_theme import plotly_layout_base

    hover_y = "%{y:$,.0f}" if y_tick_format == "usd_compact" else "%{y:.2f}"
    fig = go.Figure(
        go.Scatter(
            x=df["year"],
            y=df["value"],
            mode="lines",
            line=dict(color="#a5b4fc", width=2),
            hovertemplate="Year: %{x}<br>" + hover_y + "<extra></extra>",
        )
    )
    tickformat = ",.0f" if y_tick_format == "usd_compact" else ".1f"
    yaxis = dict(
        title_text=y_title,
        gridcolor="#1e293b",
        zeroline=False,
        linecolor="#334155",
        tickformat=tickformat,
    )
    if y_tick_format == "usd_compact":
        yaxis["tickprefix"] = "$"
    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color="#e2e8f0")),
        **plotly_layout_base(height=360),
    )
    fig.update_xaxes(title_text="Year", gridcolor="#1e293b", zeroline=False, linecolor="#334155")
    fig.update_yaxes(**yaxis)
    return fig


def _format_production_total(tonnes: float) -> str:
    if tonnes >= 1_000_000:
        return f"{tonnes / 1_000_000:.1f}M"
    if tonnes >= 1_000:
        return f"{tonnes / 1_000:.1f}K"
    return f"{tonnes:,.0f}"


def _format_import_total(value: float) -> str:
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"${value / 1_000:.1f}K"
    return f"${value:,.0f}"


def _tooltip_labels(df) -> None:
    """Human-readable tooltip fields only."""
    prod = df["production_tonnes_latest"].fillna(0)
    imp = df["import_value_or_quantity"].fillna(0)
    elev = df["representative_elevation_m"]
    df["production_tooltip"] = prod.apply(lambda x: f"{float(x):,.0f} t" if x > 0 else "—")
    df["import_tooltip"] = imp.apply(
        lambda x: _format_import_total(float(x)) if x and float(x) > 0 else "—"
    )
    df["elevation_tooltip"] = elev.apply(
        lambda x: f"{int(round(float(x)))} m" if x == x and float(x) > 0 else "—"
    )


def render_stage1_landing():
    st.set_page_config(
        page_title="From Origin to Cup",
        page_icon=streamlit_page_icon(),
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_sidebar_theme_css()
    inject_page_theme_variant("landing")

    st.markdown(
        """
        <style>
        .block-container {
          padding-top: 1.2rem;
          padding-bottom: 1.1rem;
          /* Stat cards: wider strip; prose + imports chart share the narrative measure */
          --landing-strip-max: 1120px;
          --landing-prose-max: 920px;
        }
        /* Landing narrative only: tighter measure; map/charts/cards stay full width. */
        .landing-prose {
          max-width: var(--landing-prose-max);
          margin-left: auto;
          margin-right: auto;
          width: 100%;
          box-sizing: border-box;
        }
        /* Slightly wider side inset for narrative blocks below the map */
        .landing-prose.landing-prose-postmap,
        .landing-prose-postmap {
          padding-left: 1.2rem;
          padding-right: 1.2rem;
          box-sizing: border-box;
        }
        /* Stat cards: wider than prose (920px), narrower than full-width map */
        .landing-stat-wrap {
          max-width: var(--landing-strip-max);
          margin-left: auto;
          margin-right: auto;
          width: 100%;
          box-sizing: border-box;
        }
        /* Imports time series: same max width as .landing-prose */
        section[data-testid="stMain"] [data-testid="stPlotlyChart"] {
          max-width: var(--landing-prose-max);
          margin-left: auto !important;
          margin-right: auto !important;
          width: 100%;
          box-sizing: border-box;
        }
        /*
         * Landing hero (top intro only): scoped to #landing-hero-root so Streamlit markdown wrappers
         * do not affect any other stMarkdownContainer on the page.
         */
        /* Column centered on the page; copy left-aligned inside (editorial rag) */
        #landing-hero-root.landing-hero-stack {
          text-align: left;
          padding: 0.2rem 0 0.55rem 0;
          margin-bottom: 0.15rem;
          width: 100%;
          max-width: var(--landing-prose-max);
          margin-left: auto !important;
          margin-right: auto !important;
          box-sizing: border-box;
        }
        /* Only the markdown block that wraps this hero */
        section[data-testid="stMain"] [data-testid="stMarkdownContainer"]:has(#landing-hero-root) {
          display: flex !important;
          flex-direction: column !important;
          align-items: center !important;
          width: 100% !important;
        }
        section[data-testid="stMain"] [data-testid="stMarkdownContainer"]:has(#landing-hero-root) > * {
          width: 100% !important;
          max-width: var(--landing-prose-max) !important;
          margin-left: auto !important;
          margin-right: auto !important;
          box-sizing: border-box !important;
        }
        #landing-hero-root .landing-hero-title-wrap {
          text-align: center;
          padding: 0.1rem 0 0 0;
        }
        #landing-hero-root .landing-hero-title {
          font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
          font-size: clamp(2.05rem, 4.8vw, 2.95rem);
          font-weight: 780;
          letter-spacing: -0.03em;
          line-height: 1.12;
          margin: 0;
          color: #eef2f6;
          filter: drop-shadow(0 2px 14px rgba(0, 0, 0, 0.45)) drop-shadow(0 0 28px rgba(212, 165, 116, 0.12));
          background: linear-gradient(
            118deg,
            #e8ecf1 0%,
            #f2e6d8 18%,
            #e0b878 42%,
            #c08457 58%,
            #a86b4a 72%,
            #d8dce4 100%
          );
          background-size: 220% auto;
          -webkit-background-clip: text;
          background-clip: text;
          -webkit-text-fill-color: transparent;
          animation: landingHeroTitleShimmer 14s ease-in-out infinite;
        }
        @keyframes landingHeroTitleShimmer {
          0%, 100% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
        }
        @media (prefers-reduced-motion: reduce) {
          #landing-hero-root .landing-hero-title { animation: none !important; background-position: 50% 50% !important; }
        }
        #landing-hero-root .landing-hero-title-underline {
          height: 3px;
          width: min(200px, 52vw);
          margin: 0 auto;
          border-radius: 999px;
          background: linear-gradient(
            90deg,
            transparent 0%,
            rgba(125, 156, 125, 0.5) 12%,
            rgba(212, 165, 116, 0.95) 45%,
            rgba(120, 72, 48, 0.9) 78%,
            transparent 100%
          );
          opacity: 0.95;
        }
        #landing-hero-root .landing-hero-eyebrow {
          margin: 1.35rem 0 0.4rem 0;
          width: 100%;
          max-width: none;
          font-size: 0.68rem;
          font-weight: 650;
          letter-spacing: 0.2em;
          text-transform: uppercase;
          color: rgba(168, 156, 138, 0.75);
          text-align: center;
        }
        #landing-hero-root .landing-hero-deck {
          margin: 0 0 1.35rem 0;
          max-width: 100%;
          font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
          font-size: clamp(1.32rem, 3.2vw, 1.72rem);
          font-weight: 600;
          letter-spacing: -0.025em;
          line-height: 1.22;
          color: #eef1f0;
          text-align: left;
          text-shadow: 0 1px 22px rgba(0, 0, 0, 0.35);
        }
        #landing-hero-root .landing-hero-kicker {
          margin: 0 0 0.7rem 0;
          max-width: 100%;
          font-size: 1.02rem;
          font-weight: 500;
          line-height: 1.58;
          color: #e4e9ef;
          text-align: left;
        }
        #landing-hero-root .landing-hero-support {
          margin: 0;
          max-width: 100%;
          font-size: 0.96rem;
          font-weight: 400;
          line-height: 1.62;
          color: #b9c2ce;
          text-align: left;
        }
        #landing-hero-root .landing-hero-title-beans {
          display: block;
          margin: 0.5rem auto 0.42rem auto;
          width: min(168px, 48vw);
          height: auto;
          opacity: 0.48;
        }
        .hero-note {margin-top: 4px; margin-bottom: 8px; color: #9ea8b7; font-size: 0.88rem;}
        .landing-map-legend {
          display: flex;
          flex-wrap: wrap;
          gap: 14px;
          align-items: center;
          justify-content: center;
          margin-top: 4px;
          margin-bottom: 10px;
        }
        .stat-card-row {display:flex; gap:12px; margin: 2px 0 10px 0; flex-wrap:wrap;}
        .stat-card {flex:1 1 160px; padding:8px 10px; border-radius:10px; border:1px solid rgba(255,255,255,0.06); background:rgba(15,23,42,0.82);}
        .stat-label {font-size:0.7rem; letter-spacing:0.08em; text-transform:uppercase; color:#8b93a0;}
        .stat-value {font-size:1.12rem; font-weight:600; color:#f9fafb; margin-top:2px;}
        .stat-caption {font-size:0.75rem; color:#7c8494; margin-top:2px; line-height:1.35;}
        .story-block {margin-top: 26px; color: #d1d7e0; font-size: 0.97rem; line-height: 1.68;}
        .story-block p { margin: 0 0 0.85rem 0; }
        .story-handoff {
          margin: 0.5rem 0 0 0 !important;
          padding-top: 0.15rem;
          color: #c4cad4;
          font-size: 0.93rem;
          font-weight: 500;
          line-height: 1.55;
          letter-spacing: 0.01em;
        }
        .story-heading {font-size: 1.08rem; font-weight: 650; color: #eef2f6; margin-bottom: 10px; letter-spacing: -0.02em;}
        .us-ts-section {margin-top: 30px; color: #d1d7e0; font-size: 0.97rem; line-height: 1.68;}
        .us-ts-heading {font-size: 1.08rem; font-weight: 650; color: #eef2f6; margin-bottom: 10px; letter-spacing: -0.02em;}
        .us-ts-takeaway {color: #aeb6c4; font-size: 0.93rem; margin: 14px 0 0 0; line-height: 1.6;}
        .us-ts-handoff {
          margin: 0.65rem 0 0 0;
          color: #b9c2ce;
          font-size: 0.93rem;
          line-height: 1.58;
        }
        .us-ts-source {
          color: #4b5563;
          font-size: 0.62rem;
          margin: 1.1rem 0 2.25rem 0;
          line-height: 1.42;
          opacity: 0.88;
        }
        .landing-footer-breather { height: 0.35rem; }
"""
        + MAIN_CHAPTER_FOOTER_CSS
        + """
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
<div id="landing-hero-root" class="landing-prose landing-hero-stack">
  <div class="landing-hero-title-wrap">
    <h1 class="landing-hero-title">From Origin to Cup</h1>
    <svg class="landing-hero-title-beans" viewBox="0 0 220 26" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <g>
        <ellipse cx="38" cy="13" rx="12" ry="7.5" fill="#6d9070" transform="rotate(-14 38 13)" opacity="0.65"/>
        <ellipse cx="78" cy="13" rx="12" ry="7.5" fill="#c4b896" transform="rotate(10 78 13)" opacity="0.65"/>
        <ellipse cx="118" cy="13" rx="12" ry="7.5" fill="#b88350" transform="rotate(-8 118 13)" opacity="0.65"/>
        <ellipse cx="158" cy="13" rx="12" ry="7.5" fill="#7a4a32" transform="rotate(12 158 13)" opacity="0.65"/>
        <ellipse cx="198" cy="13" rx="12" ry="7.5" fill="#2c2220" transform="rotate(-6 198 13)" opacity="0.55"/>
      </g>
    </svg>
    <div class="landing-hero-title-underline" aria-hidden="true"></div>
  </div>
  <p class="landing-hero-eyebrow">An import story</p>
  <p class="landing-hero-deck">Where American coffee actually comes from</p>
  <p class="landing-hero-kicker">
    The United States drinks coffee at a scale few countries can match, while growing almost none of what fills the cup.
    That imbalance matters more than any tasting note. Coffee here starts as imports. Only later does it become menus,
    bag copy, or a “single-origin” line on the shelf.
  </p>
  <p class="landing-hero-support">
    Treat this view as an opening frame, not the full argument. It shows where producing countries surface in U.S. buying,
    already shaped by scale, trade routes, and habit. The regional chapters continue from there, from label toward land,
    trade, and what actually shows up in the cup.
  </p>
</div>
        """,
        unsafe_allow_html=True,
    )

    df_all = load_stage1_data()

    with st.sidebar:
        render_chapter_nav_links()
        st.markdown("---")
        st.markdown(
            '<p class="sbar-section-label sbar-section-label--spaced">Map</p>',
            unsafe_allow_html=True,
        )
        st.caption("Filter the view; circle size reflects production scale.")
        region_filter = st.selectbox(
            "Region",
            ["All", "Americas", "Africa", "Asia-Pacific"],
            index=0,
            label_visibility="visible",
        )
        show_routes = st.toggle("Show routes to U.S.", value=True)

    df = df_all.copy()
    if region_filter != "All":
        df = df[df["region"] == region_filter].copy()

    n_countries = int(df["country"].nunique()) if "country" in df.columns else 0
    total_prod = float(df["production_tonnes_latest"].fillna(0).sum())
    total_import = float(df["import_value_or_quantity"].fillna(0).sum())
    prod_display = _format_production_total(total_prod)
    imp_display = _format_import_total(total_import)

    st.markdown(
        f"""
        <div class="landing-stat-wrap">
        <div class="stat-card-row">
          <div class="stat-card">
            <div class="stat-label">Countries</div>
            <div class="stat-value">{n_countries}</div>
            <div class="stat-caption">Producing countries represented in this map view.</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Production</div>
            <div class="stat-value">{prod_display}</div>
            <div class="stat-caption">Combined latest-year production across those origins.</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Import trade value</div>
            <div class="stat-value">{imp_display}</div>
            <div class="stat-caption">Combined U.S.-linked import value across those origins.</div>
          </div>
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _tooltip_labels(df)

    # Safe mode switch:
    # - interactive_backup: pydeck baseline
    # - backup_image: static fallback image
    if MAP_MODE == "backup_image" and MAP_BACKUP_IMAGE_PATH.is_file():
        st.image(str(MAP_BACKUP_IMAGE_PATH), use_container_width=True)
        st.caption("Static fallback map image (backup mode).")
    else:
        layers = build_map_layers(df, show_routes=show_routes, metric=_DEFAULT_MAP_METRIC)
        deck = pdk.Deck(
            layers=layers,
            initial_view_state=initial_view_state(),
            # MapView repeat enables horizontal world copies (continuous east/west panning).
            views=[pdk.View(type="MapView", controller=True, repeat=True)],
            map_style="mapbox://styles/mapbox/dark-v11",
            tooltip={
                "html": """
                    <b>{country}</b><br/>
                    Region: {region}<br/>
                    Production: {production_tooltip}<br/>
                    U.S. imports: {import_tooltip}<br/>
                    Elevation: {elevation_tooltip}
                """,
                "style": {"color": "white", "backgroundColor": "#222"},
            },
        )
        st.pydeck_chart(deck, use_container_width=True)

    st.markdown(
        '<div class="landing-prose landing-prose-postmap"><div class="hero-note">Routes are stylized origin-to-U.S. links for context, not shipping lanes.</div></div>',
        unsafe_allow_html=True,
    )

    shown_regions = [r for r in ["Americas", "Africa", "Asia-Pacific"] if r in set(df["region"])]
    st.markdown(
        f"""
        <div class="landing-prose-postmap">
        <div class="landing-map-legend">
          {"".join(
              [
                  f"<span style='color:rgb({REGION_COLORS[r][0]},{REGION_COLORS[r][1]},{REGION_COLORS[r][2]});font-size:0.88rem;'>● {r}</span>"
                  for r in shown_regions
              ]
          )}
          <span style="color:#f9d66f;font-size:0.88rem;">● U.S.</span>
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
<div class="story-block landing-prose landing-prose-postmap">
  <div class="story-heading">Why the U.S. cup begins elsewhere</div>
  <p>
    Coffee spread the familiar way: grown where the belt allowed, then traded into richer markets that learned producer names.
    The United States joined mainly as a buyer. What fills an American mug began in someone else’s fields and ports long before
    a roaster wrote bag copy.
  </p>
  <p>
    This view reads that split at a glance. Each circle is an origin in this slice of the trade, colored by region and scaled
    to recent production. The labels are shorthand. They point to real places. They also compress how those places show up in
    U.S. buying: what is visible, what sits in the supply chain, and what gets emphasized on the way to the shelf.
  </p>
  <p class="story-handoff">
    The map shows where dependence sits; the chart below asks how long it has held.
  </p>
</div>
        """,
        unsafe_allow_html=True,
    )

    df_imp_ts = _load_timeseries_csv(US_COFFEE_IMPORTS_TIMESERIES_PATH)
    if df_imp_ts is None:
        st.info(
            "The U.S. import time series will appear here after you run "
            "`python scripts/08_landing_us_timeseries.py` from the repository root to write the processed CSV "
            "into `data/processed/`."
        )
    else:
        st.markdown(
            """
<div class="us-ts-section landing-prose landing-prose-postmap">
  <div class="us-ts-heading">The market behind the map</div>
  <p>
    The view above answers where imported coffee comes from. This line answers how long the habit has held. Year to year, prices,
    harvests, and shocks move the trace. The through-line is steadier: the United States imports coffee at a scale domestic land
    cannot meaningfully replace. That dependence is not a blip. It is the market.
  </p>
</div>
            """,
            unsafe_allow_html=True,
        )
        from app.plotly_theme import PLOTLY_CONFIG

        fig_imp = _plotly_landing_line(
            df_imp_ts,
            title="U.S. coffee imports over time",
            y_title="Imports (million pounds)",
            y_tick_format="lbs",
        )
        st.plotly_chart(fig_imp, use_container_width=True, key="landing_imports_ts", config=PLOTLY_CONFIG)
        src_imp = df_imp_ts["source_name"].iloc[0] if "source_name" in df_imp_ts.columns else "UN Comtrade"
        st.markdown(
            f"""<div class="landing-prose landing-prose-postmap">
<div class='us-ts-takeaway'>{_imports_narrative(df_imp_ts)}</div>
<p class="us-ts-handoff">
  That steadiness raises the stakes for what follows. When the cup leans this hard on imported places, names like Colombia,
  Ethiopia, or Sumatra carry real weight in trade. How much sensory certainty they earn once you move past the label is a
  separate question. The regional chapters carry them into terrain, trade, and cup without resting on the view above as the
  last word.
</p>
<div class='us-ts-source'>{src_imp} · annual U.S. coffee imports, {int(df_imp_ts["year"].min())}–{int(df_imp_ts["year"].max())}.</div>
<div class="landing-footer-breather" aria-hidden="true"></div>
</div>""",
            unsafe_allow_html=True,
        )

    render_chapter_footer_nav()
