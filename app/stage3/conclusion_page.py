"""Closing chapter — narrative synthesis (Stage 3)."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from app.plotly_theme import PLOTLY_CONFIG
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

_ASSETS = Path(__file__).resolve().parents[2] / "assets"
_EPILOG_PHOTOS = (_ASSETS / "IMG_0017.png", _ASSETS / "IMG_0993.png")


def _hero() -> None:
    st.markdown(
        """
        <style> :root { --s3-accent: #c4b5fd; } </style>
        <div class="s2-hero" style="border-left-color: var(--s3-accent, #c4b5fd);">
          <div class="s2-kicker">✳️ &nbsp; Closing</div>
          <h1>Conclusion</h1>
          <p class="s2-lede">
            The American cup remains an import story: distant geographies, selective visibility, and labels that cannot hold every fold
            of the map. This project did not end at “flavor atlas confirmed” or “origin myth debunked.” It lands in a firmer middle:
            <strong>origin matters, though never by itself</strong>.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render() -> None:
    inject_page_theme_variant("conclusion")
    inject_region_page_css()
    sidebar_navigation("conclusion")

    st.markdown(
        """
<style>
  .s3-conclusion-breathe { height: 0.45rem; }
  .s3-epilog-band {
    border: 1px solid rgba(194, 152, 108, 0.2);
    border-radius: 12px;
    padding: 0.7rem 0.78rem 0.62rem 0.78rem;
    background:
      radial-gradient(660px 170px at 4% -12%, rgba(152, 103, 67, 0.16) 0%, transparent 62%),
      linear-gradient(180deg, rgba(35, 29, 24, 0.68) 0%, rgba(28, 24, 21, 0.58) 100%);
    box-shadow: inset 0 1px 0 rgba(255, 236, 206, 0.04);
    margin-bottom: 0.55rem;
  }
  .s3-epilog-band [data-testid="stImage"] img {
    border-radius: 10px;
    border: 1px solid rgba(196, 155, 116, 0.24);
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.2);
    filter: saturate(0.88) contrast(1.02);
  }
</style>
        """,
        unsafe_allow_html=True,
    )

    _hero()
    st.markdown('<div class="s3-conclusion-breathe" aria-hidden="true"></div>', unsafe_allow_html=True)

    st.markdown(
        """
<div class="s2-section">
  <p>
    The map showed <strong>concentration</strong>. Regional chapters put names back into land, trade, and cup. <strong>Compare</strong>
    tested what survives side by side. The durable lesson is simple: <strong>labels compress; trade, terrain, selection, and roast complicate.</strong>
  </p>
</div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="s3-conclusion-breathe" aria-hidden="true"></div>', unsafe_allow_html=True)

    section_divider()
    section_title("What this project shows")
    st.markdown(
        """
<div class="s2-section">
  <p>
    <strong>Imports still concentrate mass.</strong> A narrow band of origins—especially in the Americas slice of this extract—still carries most of what the U.S. market visibly moves.
  </p>
  <p>
    <strong>Terrain still points uphill.</strong> Representative elevations and lot altitudes keep bending toward upland belts, not accidental lowland placement. These names sit on real ridges, escarpments, plateaus, and volcanic belts.
  </p>
  <p>
    <strong>Cup identity still shows up—but faintly.</strong> Regional means separate, though less dramatically than menu shorthand suggests. Where differences appear, they read best as tendencies under conditions, not permanent flavor verdicts.
  </p>
  <p>
    <strong>Roast changes how loudly origin speaks.</strong> By the time coffee is roasted, many origin cues have already been filtered or softened. Roast can preserve clarity, round it into balance, or redirect the cup toward body, bitterness, smoke, and caramelized notes.
  </p>
</div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="s3-conclusion-breathe" aria-hidden="true"></div>', unsafe_allow_html=True)

    section_divider()
    section_title("What this means for U.S. coffee consumers")
    st.markdown(
        """
<div class="s2-section">
  <p>
    Most people meet coffee through <strong>country names, blend lines, and flavor adjectives</strong> on packaging. That language is
    not always false—it is often <strong>compressed</strong>. “Ethiopia,” “Colombia,” or “Indonesia” can each hide wide internal range.
  </p>
  <p>
    The better habit is neither blind trust nor performative skepticism, but <strong>better reading</strong>: what altitude story is implied,
    what traceability is shown, what <strong>roast style</strong> is shaping the cup, and what remains unsaid.
  </p>
  <p>
    Treat origin as a <strong>doorway into the cup</strong>, not a guarantee.
  </p>
</div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="s3-conclusion-breathe" aria-hidden="true"></div>', unsafe_allow_html=True)

    section_divider()
    section_title("What this means for producing regions")
    st.markdown(
        """
<div class="s2-section">
  <p>
    Producing regions live in a tension between <strong>commodity heft</strong> and <strong>narrative visibility</strong>. High-volume origins anchor
    price, supply, and availability; smaller or story-rich origins can register much louder in U.S. café culture than tonnage alone predicts.
  </p>
  <p>
    Market visibility is not ledger dominance. <strong>Café mindshare tracks mass only in part</strong>; it also tracks reputation,
    scarcity, altitude storytelling, retail framing, and roast style.
  </p>
</div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="s3-conclusion-breathe" aria-hidden="true"></div>', unsafe_allow_html=True)

    section_divider()
    section_title("Limits and interpretation")
    st.markdown(
        """
<div class="s2-section">
  <p>
    This app works through <strong>windowed evidence</strong>. Cupping rows are <strong>sampled Arabica lots</strong>, not whole harvests.
    Growing-region markers are <strong>illustrative</strong>, not audited farm coordinates. Trade values are <strong>study totals</strong>,
    not rebuilt customs files. Regional language is convenience, not proof of internal uniformity—and cup differences never arrive untouched by roast, selection, or sampling.
  </p>
</div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="s3-conclusion-breathe" aria-hidden="true"></div>', unsafe_allow_html=True)

    section_divider()
    section_title("Market weight at a glance")
    st.markdown(
        """
<div class="s2-section">
  <p>
    One last bar chart—<strong>memory aid, not new evidence</strong>. Most visible production mass in this extract still sits with the Americas.
    Keep that bookmark, but not as a full explanation: <strong>weight in the ledger and weight in the imagination do not always match</strong>.
  </p>
</div>
        """,
        unsafe_allow_html=True,
    )

    prod_r = cd.production_totals_by_region()
    fig = ch.fig_production_share_bars(
        prod_r,
        title="Share of production tonnage in this study",
    )
    st.plotly_chart(fig, use_container_width=True, key="conclusion_production_share", config=PLOTLY_CONFIG)
    st.markdown('<div class="s3-conclusion-breathe" aria-hidden="true"></div>', unsafe_allow_html=True)

    section_divider()
    section_title("Closing")
    st.markdown(
        """
<div class="s2-section">
  <p>
    If one line stays with you, let it be this: <strong>the American cup is an import story told through unevenly visible geographies.</strong>
    Origin names matter—but as <strong>starting points, not final explanations</strong>.
  </p>
  <p>
    What reaches the mug has already passed through trade, terrain, selection, and roast. Read origin names as <strong>doorways, not endings</strong>—and stay curious longer than the label asks.
  </p>
</div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="s3-conclusion-breathe" aria-hidden="true"></div>', unsafe_allow_html=True)

    if all(p.is_file() for p in _EPILOG_PHOTOS):
        st.markdown('<div class="s3-epilog-band">', unsafe_allow_html=True)
        st.markdown(
            """
<div class="s2-section">
  <p style="color:#94a3b8;font-size:13px;margin:0 0 0.85rem 0;">
    After all the maps, metrics, and origin stories, it still ends here: people sharing coffee.
  </p>
</div>
            """,
            unsafe_allow_html=True,
        )
        c1, c2 = st.columns(2, gap="medium")
        with c1:
            st.image(str(_EPILOG_PHOTOS[0]), use_container_width=True)
        with c2:
            st.image(str(_EPILOG_PHOTOS[1]), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    chapter_footer_full_arc()
