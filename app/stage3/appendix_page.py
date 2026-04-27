"""Appendix — sources, supplementary views, disclosure (sidebar only; not in footer nav)."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.config import REGION_COLORS
from app.plotly_theme import PLOTLY_CONFIG, plotly_layout_base
from app.stage2 import region_data as rd
from app.stage2.region_shell import inject_region_page_css, section_divider, section_title, sidebar_navigation
from app.stage3 import compare_data as cd


def _region_hex(name: str) -> str:
    rgb = REGION_COLORS.get(name, (148, 163, 184))
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


def _appendix_css() -> None:
    st.markdown(
        """
<style>
  .appendix-ref {
    border: 1px solid rgba(148,163,184,0.14);
    border-radius: 10px;
    padding: 1rem 1.15rem;
    margin-bottom: 1rem;
    background: rgba(255,255,255,0.02);
  }
  .appendix-ref h4 {
    margin: 0 0 0.45rem 0;
    font-size: 1.02rem;
    font-weight: 600;
    color: #e2e8f0;
    letter-spacing: -0.01em;
  }
  .appendix-ref .meta { font-size: 0.88rem; color: #94a3b8; line-height: 1.52; margin: 0.2rem 0; }
  .appendix-ref .meta strong { color: #cbd5e1; font-weight: 600; }
  .appendix-spacer { height: 0.55rem; }
  .appendix-ai-log { margin-top: 0.35rem; }
</style>
        """,
        unsafe_allow_html=True,
    )


def _ref_card(
    title: str,
    type_line: str,
    used: str,
    notes: str,
    *,
    link: str | None = None,
    link_label: str | None = None,
    access_note: str | None = None,
) -> None:
    access_html = ""
    if link:
        label = link_label or "Source page"
        access_html = (
            f'<p class="meta"><strong>Access:</strong> '
            f'<a href="{link}" target="_blank" rel="noopener noreferrer">{label}</a></p>'
        )
    elif access_note:
        access_html = f'<p class="meta"><strong>Access:</strong> {access_note}</p>'
    st.markdown(
        f"""
<div class="appendix-ref">
  <h4>{title}</h4>
  <p class="meta"><strong>Type:</strong> {type_line}</p>
  <p class="meta"><strong>Used for:</strong> {used}</p>
  <p class="meta"><strong>Notes:</strong> {notes}</p>
  {access_html}
</div>
        """,
        unsafe_allow_html=True,
    )


def _fig_representative_elevation_by_region() -> go.Figure | None:
    """One value per origin country (terrain context), overlaid by region—not lot-level altitude."""
    elev = rd.load_elevation_context()
    prod = rd.load_stage1_production()
    if elev.empty or prod.empty or "representative_elevation_m" not in elev.columns:
        return None
    if "country" not in elev.columns or "country" not in prod.columns or "region" not in prod.columns:
        return None
    m = elev[["country", "representative_elevation_m"]].merge(
        prod[["country", "region"]].drop_duplicates("country"),
        on="country",
        how="inner",
    )
    m = m[m["region"].isin(cd.REGIONS_ORDER)]
    fig = go.Figure()
    for reg in cd.REGIONS_ORDER:
        sub = m.loc[m["region"] == reg, "representative_elevation_m"].astype(float).dropna()
        sub = sub[(sub > 0) & (sub < 6000)]
        if len(sub) < 1:
            continue
        fig.add_trace(
            go.Histogram(
                x=sub,
                name=reg,
                opacity=0.48,
                nbinsx=max(8, min(24, len(sub) * 2)),
                marker_color=_region_hex(reg),
                histnorm="probability density",
            )
        )
    if not fig.data:
        return None
    fig.update_layout(
        title=dict(
            text="Representative country elevation (m) — density by region",
            font=dict(size=14, color="#e2e8f0"),
        ),
        barmode="overlay",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        **plotly_layout_base(height=400),
    )
    fig.update_xaxes(
        title_text="Representative elevation (m) — one value per country",
        gridcolor="#1e293b",
        zeroline=False,
        linecolor="#334155",
    )
    fig.update_yaxes(title_text="Density", gridcolor="#1e293b", zeroline=False, linecolor="#334155")
    return fig


def _fig_total_cup_points_by_region(cup: pd.DataFrame) -> go.Figure | None:
    if cup.empty or "total_cup_points" not in cup.columns:
        return None
    fig = go.Figure()
    for reg in cd.REGIONS_ORDER:
        sub = cup.loc[cup["region"] == reg, "total_cup_points"].dropna()
        if len(sub) < 2:
            continue
        fig.add_trace(
            go.Histogram(
                x=sub,
                name=reg,
                opacity=0.48,
                nbinsx=28,
                marker_color=_region_hex(reg),
                histnorm="probability density",
            )
        )
    if not fig.data:
        return None
    fig.update_layout(
        title=dict(text="Total cup points — density by region", font=dict(size=14, color="#e2e8f0")),
        barmode="overlay",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        **plotly_layout_base(height=400),
    )
    fig.update_xaxes(title_text="Total cup points", gridcolor="#1e293b", zeroline=False, linecolor="#334155")
    fig.update_yaxes(title_text="Density", gridcolor="#1e293b", zeroline=False, linecolor="#334155")
    return fig


def _fig_top_countries_lot_counts(cup: pd.DataFrame) -> go.Figure | None:
    if cup.empty or "country" not in cup.columns:
        return None
    cts = cup.groupby("country").size().sort_values(ascending=True).tail(14)
    if cts.empty:
        return None
    fig = go.Figure(
        go.Bar(
            x=cts.values,
            y=cts.index.astype(str),
            orientation="h",
            marker=dict(color="rgba(148,163,184,0.55)", line=dict(color="rgba(148,163,184,0.35)", width=1)),
        )
    )
    fig.update_layout(
        title=dict(text="Lots in this extract — top countries by count", font=dict(size=14, color="#e2e8f0")),
        **plotly_layout_base(height=420),
    )
    fig.update_xaxes(title_text="Number of cupping rows", gridcolor="#1e293b", zeroline=False, linecolor="#334155")
    fig.update_yaxes(title_text="", gridcolor="#1e293b", zeroline=False, linecolor="#334155", automargin=True)
    return fig


def _hero() -> None:
    st.markdown(
        """
        <style> :root { --s3-accent: #94a3b8; } </style>
        <div class="s2-hero" style="border-left-color: var(--s3-accent, #94a3b8);">
          <div class="s2-kicker">📎 &nbsp; TECHNICAL APPENDIX</div>
          <h1>Appendix</h1>
          <p class="s2-lede">
            Sources, extra views, and disclosures.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render() -> None:
    inject_region_page_css()
    _appendix_css()
    sidebar_navigation("appendix")

    _hero()

    section_title("References")
    _ref_card(
        "Arabica cup-quality dataset (coffee_features)",
        "Processed lot-level cupping table (Kaggle-derived pipeline into this project).",
        "Regional profiles, Compare sensory views, lot altitude and score summaries.",
        "Rows are grading-table samples, not a census of every export bag.",
        link="https://www.kaggle.com/datasets/fedesoriano/coffee-quality-dataset",
        link_label="Kaggle — Coffee Quality Dataset",
    )
    _ref_card(
        "Our World in Data — coffee bean production",
        "Public country-level production time series.",
        "Stage 1 production tonnage, map marker sizing, regional production share.",
        "Processed in-repo as data/processed/stage1_country_production.csv.",
        link="https://ourworldindata.org/grapher/coffee-bean-production",
        link_label="OWID grapher page",
    )
    _ref_card(
        "U.S.-linked import extract",
        "Curated trade-by-origin table (simplified totals from project ingest).",
        "Arc weights toward the U.S.; import bars alongside production in regional chapters.",
        "Re-export hubs excluded in pipeline code; figures are illustrative trade structure, not port-level customs.",
        access_note="Raw paths vary by ingest; see data/raw/trade or data/external for the study extract.",
    )
    _ref_card(
        "Natural Earth — country boundaries",
        "110m cultural vectors (admin boundaries).",
        "Country outlines, projected centroids, Stage 1 GeoJSON and centroid CSV.",
        "Consistent map geometry and origin placement.",
        link="https://www.naturalearthdata.com/downloads/110m-cultural-vectors/",
        link_label="Natural Earth downloads",
    )
    _ref_card(
        "GMTED2010 terrain elevation (USGS)",
        "Global DEM (15 arc-second tiles, clipped per study country).",
        "Stage 2 hillshade terrain maps and elevation context.",
        "Country clips live under data/raw/elevation/.",
        link="https://www.usgs.gov/coastal-changes-hazards-portal/science/global-multi-resolution-terrain-elevation-data-2010-gmted2010",
        link_label="USGS — GMTED2010",
    )
    _ref_card(
        "Country elevation context",
        "Summary table: one representative elevation (m ASL) per origin country.",
        "Terrain medians and country callouts versus lot-reported altitude in cup rows.",
        "National-scale context; not a substitute for farm-level GPS.",
        access_note="data/external/country_elevation_context.csv",
    )
    _ref_card(
        "Illustrative growing-region samples",
        "Generated point table for terrain map overlays.",
        "Red markers on regional Stage 2 DEM maps.",
        "Elevation-constrained samples for narrative legibility; not audited farm coordinates.",
        access_note="data/processed/stage2_country_growing_points.csv",
    )
    _ref_card(
        "USDA ERS — food availability (imports)",
        "Official annual U.S. supply/use table (CSV series).",
        "Landing-page long-run U.S. coffee import line.",
        "Written to data/processed/us_coffee_imports_timeseries.csv in this repo.",
        link="https://www.ers.usda.gov/data-products/food-availability-per-capita-data-system/",
        link_label="USDA ERS Food Availability System",
    )
    _ref_card(
        "U.S. Census — County Business Patterns (NAICS 722515)",
        "API-derived U.S. establishment counts.",
        "Landing-page storefront proxy alongside the import series.",
        "Beverage-bar NAICS category—structural proxy, not a literal “coffee-only café” census.",
        link="https://www.census.gov/programs-surveys/cbp.html",
        link_label="U.S. Census — CBP program",
    )
    st.markdown('<div class="appendix-spacer" aria-hidden="true"></div>', unsafe_allow_html=True)
    section_divider()
    section_title("Supplementary information")

    st.markdown(
        """
<div class="s2-section">
  <p><strong>A. Notes on interpretation</strong></p>
  <p>
    <strong>Production vs import slice.</strong> Production sums origin-side mass in the curated country list; the
    U.S.-linked import column is a normalized mirror—good for structure, not full trade accounting.
  </p>
  <p>
    <strong>Representative terrain vs lot altitude.</strong> GMTED maps and country context summarize upland shape; cup
    rows carry marketer- or grader-reported lot altitude—same vocabulary, different objects.
  </p>
  <p>
    <strong>Cup sample vs export reality.</strong> Cupping rows skew toward Arabica lots that reached a grading table;
    they are not a portrait of every bag shipped.
  </p>
  <p>
    <strong>Regional labels.</strong> “Africa,” “Americas,” and “Asia-Pacific” organize the narrative; each label still
    wraps a lot of internal geography.
  </p>
</div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="appendix-spacer" aria-hidden="true"></div>', unsafe_allow_html=True)
    st.markdown('<p class="s2-section-title" style="margin-top:0.5rem;">B. Additional supporting visuals</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="s2-muted">Country-level representative elevation from country_elevation_context.csv, split by '
        "world region—national terrain context, not marketing lot altitude.</p>",
        unsafe_allow_html=True,
    )

    fe = _fig_representative_elevation_by_region()
    if fe is not None:
        st.plotly_chart(fe, use_container_width=True, key="appendix_rep_elev_hist", config=PLOTLY_CONFIG)
    else:
        st.caption("Skipped: missing elevation context or production merge.")

    try:
        cup = cd.cup_features_by_region()
    except FileNotFoundError:
        cup = pd.DataFrame()
        st.info("Cup-quality features file not found; remaining supplementary charts are skipped.")

    fc = _fig_total_cup_points_by_region(cup)
    if fc is not None:
        st.plotly_chart(fc, use_container_width=True, key="appendix_cup_points_hist", config=PLOTLY_CONFIG)
    else:
        st.caption("Skipped: not enough cup-point data by region.")

    fb = _fig_top_countries_lot_counts(cup)
    if fb is not None:
        st.plotly_chart(fb, use_container_width=True, key="appendix_country_counts", config=PLOTLY_CONFIG)
    else:
        st.caption("Skipped: insufficient country-level lot counts.")

    st.markdown('<div class="appendix-spacer" aria-hidden="true"></div>', unsafe_allow_html=True)
    section_divider()
    section_title("AI usage log")
    st.markdown(
        """
<div class="s2-section appendix-ai-log">
  <ul>
    <li>Brainstorming and comparing potential public datasets and documentation for where to pull each metric</li>
    <li>Drafting the Appendix references card template (fields, tone, and what to list vs omit)</li>
    <li>Map layer and trade-flow experimentation, including PyDeck / <code>PathLayer</code> route rendering</li>
    <li>Weighing a deck.gl / PyDeck-style approach versus heavier Folium / Leaflet-style prototypes for this app</li>
    <li>Elevation-map layout ideas, hillshade framing, and linked dropdown / view-state refinement</li>
    <li>Roast infographic structure, spacing, temperature-axis labeling, and SVG iteration</li>
    <li>Compare / Conclusion / Appendix page layout suggestions and section ordering checks</li>
    <li>Streamlit component wiring patterns (charts, expanders, sidebar vs footer navigation) and integration nits</li>
    <li>Page styling integration hints (spacing, dividers, muted captions) matched to the existing dark theme</li>
    <li>Proofreading, concision passes, and light grammar cleanup on in-app copy</li>
    <li>Icon and emoji choices for sidebar labels and section kickers where they improved scanability</li>
    <li>Debugging ideas for interactive Plotly / PyDeck issues and empty-state handling</li>
  </ul>
</div>
        """,
        unsafe_allow_html=True,
    )
