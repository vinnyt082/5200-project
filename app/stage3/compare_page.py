"""Cross-region comparison chapter (Stage 3)."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from app.plotly_theme import PLOTLY_CONFIG
from app.stage2 import region_data as rd
from app.stage2.region_shell import (
    chapter_footer_full_arc,
    inject_page_theme_variant,
    inject_region_page_css,
    section_divider,
    section_title,
    sidebar_navigation,
)
from app.stage3 import compare_data as cd
from app.stage3 import stage3_charts as ch

_ROAST_INFOGRAPHIC_SVG = (
    Path(__file__).resolve().parents[2] / "assets" / "infographics" / "roast_progression_infographic.svg"
)


def _roast_progression_infographic() -> None:
    """Roast bridge + progression asset (scripts/09_roast_progression_infographic.py)."""
    st.markdown(
        """
<div class="s2-section">
  <p>
    <strong>Origin</strong> sets field potential; <strong>roast</strong> decides how much of that potential stays audible.
    The same country on a label can land in very different places along the arc below.
  </p>
  <p style="color:#94a3b8;font-size:13px;margin:0;">
    Read left to early roast, right toward deeper development; the right edge adds quiet °F anchors for where stages
    often land—ballpark context, not a control chart.
  </p>
</div>
        """,
        unsafe_allow_html=True,
    )
    if not _ROAST_INFOGRAPHIC_SVG.is_file():
        st.caption("Roast progression graphic missing — run `python scripts/09_roast_progression_infographic.py`.")
        return
    # Inline SVG via markdown is stripped by Streamlit’s HTML sanitizer (paths/text/filters
    # removed), which produced an empty “card” shell. st.image renders the full SVG file.
    st.markdown('<div class="s3-roast-frame">', unsafe_allow_html=True)
    st.image(str(_ROAST_INFOGRAPHIC_SVG), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown(
        """
<div class="s2-section">
  <p>
    Origin still matters, but <strong>roast sets the volume</strong>: regional contrast is easiest to hear when roast
    preserves lift and clarity, and much harder to read when development drives the cup toward body, bitterness, and smoke.
  </p>
</div>
        """,
        unsafe_allow_html=True,
    )


def _synthesis_hero() -> None:
    st.markdown(
        """
        <style> :root { --s3-accent: #94a3b8; } </style>
        <div class="s2-hero" style="border-left-color: var(--s3-accent, #94a3b8);">
          <div class="s2-kicker">⚖️ &nbsp; Synthesis</div>
          <h1>Compare</h1>
          <p class="s2-lede">
            Three regions, one import-fed market. The regional chapters read each geography on its own terms; here the test is what
            survives when all three sit in one frame. Scale, terrain, altitude, cup averages, and roast are read together to see
            which differences hold, which collapse, and what actually reaches the cup.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render() -> None:
    inject_page_theme_variant("compare")
    inject_region_page_css()
    sidebar_navigation("compare")

    st.markdown(
        """
<style>
  .s3-compare-breathe { height: 0.5rem; }
  .s3-roast-frame {
    border: 1px solid rgba(183, 145, 102, 0.22);
    border-radius: 12px;
    padding: 0.45rem 0.52rem 0.28rem 0.52rem;
    margin: 0.35rem 0 0.4rem 0;
    background:
      radial-gradient(560px 160px at 100% -6%, rgba(126, 95, 70, 0.12) 0%, transparent 62%),
      rgba(27, 25, 24, 0.5);
  }
</style>
        """,
        unsafe_allow_html=True,
    )

    _synthesis_hero()

    st.markdown(
        """
<div class="s2-section">
  <p>
    The regional chapters handled each geography on its own terms. Here the question changes: not what each region looks like alone,
    but what survives when all three are read together. This is a stress test across layers at once—scale, terrain, altitude,
    cup averages, and then roast as the downstream filter that can either <strong>preserve</strong> origin cues or start <strong>talking over</strong> them.
  </p>
</div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="s3-compare-breathe" aria-hidden="true"></div>', unsafe_allow_html=True)

    prod_r = cd.production_totals_by_region()
    imp_r = cd.import_totals_by_region()
    elev_med = cd.median_representative_elevation_by_region()
    cup = cd.cup_features_by_region()
    sens = cd.sensory_means_by_region()
    reg_summary = cd.regional_lot_altitude_score_summary()

    # --- Scale & trade ---
    section_title("Scale and trade")
    st.markdown('<div class="s3-compare-breathe" aria-hidden="true"></div>', unsafe_allow_html=True)
    st.markdown(
        """
<div class="s2-section">
  <p>
    Start with structural weight, where differences separate most cleanly. <strong>Americas</strong> lead production among mapped origins;
    <strong>Asia-Pacific</strong> stays large; <strong>Africa</strong> remains lighter in tonnage in this extract. The U.S.-linked import slice
    then shifts the ranking logic: not a corrected final table, but a different lens on importance. Production, import structure,
    and cup identity are <strong>related views, not one ladder</strong>.
  </p>
</div>
        """,
        unsafe_allow_html=True,
    )

    _cmp_yr = rd.stage1_production_reference_year()
    _cmp_yr_s = str(_cmp_yr) if _cmp_yr is not None else "latest year"
    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.markdown(
            f'<p class="s2-muted"><strong>Production by region ({_cmp_yr_s}, million tonnes)</strong><br/>'
            "Summed across the same origin countries as the map.</p>",
            unsafe_allow_html=True,
        )
        fig_p = ch.fig_horizontal_bar_regions(
            prod_r / 1_000_000.0,
            title="Production by region",
            xlabel="Million tonnes",
            x_format="{:.2f}",
        )
        st.plotly_chart(fig_p, use_container_width=True, key="compare_production_bars", config=PLOTLY_CONFIG)
        st.caption(
            f"Million tonnes; {_cmp_yr} in production source data."
            if _cmp_yr is not None
            else "Million tonnes; latest year in production source data."
        )
    with c2:
        st.markdown(
            '<p class="s2-muted"><strong>U.S.-linked import value by region</strong><br/>'
            "Nominal dollars, billions.</p>",
            unsafe_allow_html=True,
        )
        fig_i = ch.fig_horizontal_bar_regions(
            imp_r / 1_000_000_000.0,
            title="U.S.-linked import value by region",
            xlabel="Billions (nominal dollars)",
            x_format="{:.2f}",
        )
        st.plotly_chart(fig_i, use_container_width=True, key="compare_import_bars", config=PLOTLY_CONFIG)
        st.caption("Nominal dollars in billions; read rank and spacing as structure, not port-level totals.")

    st.markdown(
        """
<div class="s2-section">
  <p>
    <strong>Americas</strong> sit heavy in <em>both</em> production and this U.S.-linked import slice. <strong>Asia-Pacific</strong>
    keeps production heft without the same mirror in the import bars. <strong>Africa</strong> stays modest in tonnage yet outsized in
    specialty language. The ranking diverges as soon as the question changes: <strong>which region “matters” depends on the lens</strong>.
  </p>
</div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="s3-compare-breathe" aria-hidden="true"></div>', unsafe_allow_html=True)

    section_divider()

    # --- Terrain ---
    section_title("Terrain and elevation")
    st.markdown('<div class="s3-compare-breathe" aria-hidden="true"></div>', unsafe_allow_html=True)
    st.markdown(
        """
<div class="s2-section">
  <p>
    <strong>Scale</strong> separates the regions cleanly; elevation does not. All three still sit in recognizably coffee-growing terrain.
    The difference is less one vertical order than how each region’s growing contexts fan out. That is why this section keeps
    two lenses side by side: representative national terrain and reported lot altitude. They overlap, but they are <strong>not the same view</strong>.
  </p>
</div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<p class="s2-muted"><strong>Linked terrain views</strong><br/>'
        "Hover a region in one panel to read both. Use the in-chart focus buttons to highlight a single region across both charts.</p>",
        unsafe_allow_html=True,
    )
    if not elev_med.empty and elev_med.notna().any() and not cup.empty and "altitude" in cup.columns and "region" in cup.columns:
        fig_linked = ch.fig_linked_terrain_altitude(
            elev_med.dropna(),
            cup,
            title="Terrain and lot-altitude by region (linked view)",
        )
        st.plotly_chart(fig_linked, use_container_width=True, key="compare_terrain_linked", config=PLOTLY_CONFIG)
    else:
        st.caption("Insufficient elevation context or lot-altitude data for linked terrain view.")

    st.markdown(
        """
<div class="s2-section">
  <p>
    The medians sit closer than many readers expect: coffee-country terrain across all three, not plains versus mountains.
    <strong>Africa</strong> reads highest here, the <strong>Americas</strong> hold a broad middle, and <strong>Asia-Pacific</strong>
    centers lower with roomy internal spread. The stronger read is not a winner at the center line, but <strong>how differently each region’s growing contexts fan out</strong>.
    Africa’s box draws on fewer lots in this extract, so read it as indicative, not definitive.
  </p>
  <p>
    This is where terrain complicates what trade bars can invite: labels often flatten spread into one altitude story when the land does not.
  </p>
</div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="s3-compare-breathe" aria-hidden="true"></div>', unsafe_allow_html=True)

    section_divider()

    # --- Cup character & roast ---
    section_title("Cup character and roast")
    st.markdown('<div class="s3-compare-breathe" aria-hidden="true"></div>', unsafe_allow_html=True)
    st.markdown(
        """
<div class="s2-section">
  <p>
    Regional sensory averages do <strong>separate</strong>, but only <strong>modestly</strong>. No region owns every trait.
    The gaps are enough for family resemblance, not enough for tidy regional flavor cartoons. Even those modest differences are not what a drinker meets in pure form:
    by the time coffee reaches the cup, <strong>roast</strong> is one of the loudest downstream levers.
  </p>
</div>
        """,
        unsafe_allow_html=True,
    )

    if not sens.empty:
        st.markdown(
            '<p class="s2-muted"><strong>Regional cup traits</strong><br/>'
            "Means in this extract; color marks distance from the three-region average per attribute. "
            "<strong>Read small gaps, not a medal table.</strong></p>",
            unsafe_allow_html=True,
        )
        fig_s = ch.fig_sensory_heatmap_regions(
            sens,
            attrs=["acidity", "flavor", "body", "sweetness"],
            title="Mean sensory traits by region",
        )
        st.plotly_chart(fig_s, use_container_width=True, key="compare_sensory_heatmap", config=PLOTLY_CONFIG)
    else:
        st.info("Sensory aggregates not available.")

    st.markdown(
        """
<div class="s2-section">
  <p>
    Regional means diverge <strong>lightly</strong>. <strong>Acidity</strong> and <strong>flavor</strong> can separate by a few tenths;
    <strong>body</strong> stays tight. That supports family resemblance, not stereotype confirmed.
  </p>
  <p>
    Then the downstream turn matters: roast can preserve brightness and origin clarity, soften them into balance, or redirect the cup toward body,
    bitterness, smoke, and caramelized flavors. Origin sets field potential; roast decides how audible that potential remains.
  </p>
</div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="s3-compare-breathe" aria-hidden="true"></div>', unsafe_allow_html=True)

    _roast_progression_infographic()

    section_divider()
    st.markdown('<div class="s3-compare-breathe" aria-hidden="true"></div>', unsafe_allow_html=True)

    # --- Final synthesis ---
    section_title("Three regions in one view")
    st.markdown('<div class="s3-compare-breathe" aria-hidden="true"></div>', unsafe_allow_html=True)
    st.markdown(
        """
<div class="s2-section">
  <p>
    Each region becomes a <strong>single point</strong>: median lot altitude on the x-axis, mean cup score on the y-axis.
    The compression is useful—and severe. It hides internal spread and turns mixed landscapes into one dot, so this works as a
    <strong>last glance, not a verdict</strong>.
  </p>
</div>
        """,
        unsafe_allow_html=True,
    )

    if not reg_summary.empty:
        st.markdown(
            '<p class="s2-muted"><strong>Regions at a glance</strong><br/>'
            "One marker per region from this extract; hover for exact values.</p>",
            unsafe_allow_html=True,
        )
        fig_sc = ch.fig_scatter_region_summary(
            reg_summary,
            title="Median altitude vs mean cup score (one point per region)",
        )
        st.plotly_chart(fig_sc, use_container_width=True, key="compare_region_scatter", config=PLOTLY_CONFIG)

    st.markdown(
        """
<div class="s2-section">
  <p>
    The points drift upward where altitude and mean score rise together, but <strong>not as a fixed law</strong>. <strong>Africa</strong>
    sits highest in this compressed frame, <strong>Asia-Pacific</strong> lower and left, and the <strong>Americas</strong>
    between them in altitude without leading the score axis. Altitude helps, but it <strong>never acts alone</strong>—variety,
    processing, <strong>roast</strong>, and sample composition still steer the outcome.
  </p>
</div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="s3-compare-breathe" aria-hidden="true"></div>', unsafe_allow_html=True)

    section_divider()
    st.markdown('<div class="s3-compare-breathe" aria-hidden="true"></div>', unsafe_allow_html=True)

    section_title("What changes across regions — and what does not")
    st.markdown(
        """
<div class="s2-section">
  <p>
    <strong>What changes:</strong> <strong>Americas</strong> carry the heaviest production and U.S.-linked import weight in this view.
    <strong>Asia-Pacific</strong> remains structurally large, with only part of that scale visible in the import slice. <strong>Africa</strong>
    stays lighter in tonnage but heavier in cultural and commercial narration than mass alone would predict.
  </p>
  <p>
    <strong>What changes less:</strong> all three still sit in recognizably coffee-growing terrain, and their sensory means cluster more tightly than café storytelling usually admits.
    The durable pattern is <strong>internal spread</strong>, not fixed regional essence. Labels compress enough diversity that they work best as <strong>handles, not verdicts</strong>.
  </p>
</div>
        """,
        unsafe_allow_html=True,
    )

    section_divider()
    st.markdown('<div class="s3-compare-breathe" aria-hidden="true"></div>', unsafe_allow_html=True)

    section_title("Toward the closing chapter")
    st.markdown(
        """
<div class="s2-section">
  <p>
    The side-by-side comparison is complete; what remains is judgment. What should a reader, buyer, or drinker carry forward?
    The Conclusion now has to earn the final claim: <strong>origin still matters</strong>, but it reaches the cup through trade, terrain,
    selection, and roast—not as untouched essence.
  </p>
</div>
        """,
        unsafe_allow_html=True,
    )

    chapter_footer_full_arc()
