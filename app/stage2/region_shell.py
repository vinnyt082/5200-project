"""
Reusable layout and chrome for regional storytelling pages.

Keeps typography, hero framing, and section rhythm consistent across regions
without forcing identical content structure.
"""

from __future__ import annotations

from typing import Optional

import streamlit as st

from app.sidebar_theme import inject_sidebar_theme_css

# --- Region metadata (accent colors align with Stage 1 REGION_COLORS) -------
REGION_META = {
    "Americas": {
        "title": "Americas",
        "emoji": "🌎",
        "accent": "#e86f51",
        "accent_rgb": "232, 111, 81",
    },
    "Africa": {
        "title": "Africa",
        "emoji": "🌍",
        "accent": "#58c486",
        "accent_rgb": "88, 196, 134",
    },
    "Asia-Pacific": {
        "title": "Asia-Pacific",
        "emoji": "🌏",
        "accent": "#68a2ff",
        "accent_rgb": "104, 162, 255",
    },
}


MAP_BRIDGE_HTML = """
<div class="s2-bridge">
  <p><strong>From map to region.</strong> The home map makes the import geography visible; this
  chapter explains what those origin names mean in practice—relative scale in U.S.-linked trade,
  terrain and elevation structure, and broad cup-profile patterns. When you have read the three regions,
  <strong>Compare</strong> sets them side by side, and <strong>Conclusion</strong> names what that geography
  implies for how Americans actually meet coffee in the wild.</p>
</div>
"""

# Sidebar + bottom nav: single source (paths, labels, emoji — keep order fixed).
CHAPTER_NAV_ENTRIES: tuple[tuple[str, str, str], ...] = (
    ("streamlit_app.py", "Map", "🗺️"),
    ("pages/Americas.py", "Americas", "🌎"),
    ("pages/Africa.py", "Africa", "🌍"),
    ("pages/Asia_Pacific.py", "Asia-Pacific", "🌏"),
    ("pages/Compare.py", "Compare", "⚖️"),
    ("pages/Conclusion.py", "Conclusion", "✳️"),
)

# Appendix: sidebar only (not included in ``render_chapter_footer_nav``).
APPENDIX_SIDEBAR_LINK: tuple[str, str, str] = ("pages/Appendix.py", "Appendix", "📎")

# Main-area chapter footer (not sidebar): narrow row to prose width on landing; compact link chrome.
MAIN_CHAPTER_FOOTER_CSS = """
section[data-testid="stMain"] [data-testid="stHorizontalBlock"]:has(a[data-testid="stPageLink-NavLink"]) {
  max-width: min(var(--landing-prose-max, 920px), 100%);
  margin-left: auto !important;
  margin-right: auto !important;
  width: 100%;
  box-sizing: border-box;
}
section[data-testid="stMain"] a[data-testid="stPageLink-NavLink"] {
  padding-left: 0.22rem !important;
  padding-right: 0.22rem !important;
  gap: 0.28rem !important;
  font-size: 0.82rem !important;
  justify-content: center !important;
}
"""


_PAGE_THEME_VARIANTS: dict[str, str] = {
    "landing": """
      --coffee-bg-1: rgba(96, 133, 98, 0.16);
      --coffee-bg-2: rgba(72, 109, 74, 0.11);
      --coffee-bg-3: rgba(44, 77, 59, 0.1);
      --coffee-paper: #e9dfd2;
      --coffee-accent: #c58a55;
      --coffee-olive: #6d8b68;
      --coffee-smoke: #1f1a16;
    """,
    "americas": """
      --coffee-bg-1: rgba(86, 127, 84, 0.14);
      --coffee-bg-2: rgba(66, 101, 68, 0.1);
      --coffee-bg-3: rgba(52, 86, 65, 0.1);
      --coffee-paper: #e8ddd1;
      --coffee-accent: #cf865e;
      --coffee-olive: #6f8b6f;
      --coffee-smoke: #1d1916;
    """,
    "africa": """
      --coffee-bg-1: rgba(96, 135, 90, 0.14);
      --coffee-bg-2: rgba(72, 110, 72, 0.11);
      --coffee-bg-3: rgba(58, 92, 63, 0.1);
      --coffee-paper: #e5dccf;
      --coffee-accent: #b79466;
      --coffee-olive: #7a9a74;
      --coffee-smoke: #1b1915;
    """,
    "asia-pacific": """
      --coffee-bg-1: rgba(82, 123, 103, 0.14);
      --coffee-bg-2: rgba(63, 97, 82, 0.11);
      --coffee-bg-3: rgba(49, 82, 70, 0.1);
      --coffee-paper: #e5d8cb;
      --coffee-accent: #ab845f;
      --coffee-olive: #6d8a73;
      --coffee-smoke: #1b1917;
    """,
    "compare": """
      --coffee-bg-1: rgba(82, 116, 95, 0.13);
      --coffee-bg-2: rgba(63, 91, 79, 0.1);
      --coffee-bg-3: rgba(48, 78, 68, 0.09);
      --coffee-paper: #e1d8ce;
      --coffee-accent: #a98966;
      --coffee-olive: #70836f;
      --coffee-smoke: #1a1919;
    """,
    "conclusion": """
      --coffee-bg-1: rgba(102, 140, 100, 0.15);
      --coffee-bg-2: rgba(78, 112, 79, 0.11);
      --coffee-bg-3: rgba(56, 88, 66, 0.1);
      --coffee-paper: #ece0d2;
      --coffee-accent: #ca9464;
      --coffee-olive: #738b6e;
      --coffee-smoke: #1f1a17;
    """,
    "default": """
      --coffee-bg-1: rgba(92, 129, 93, 0.13);
      --coffee-bg-2: rgba(69, 103, 74, 0.1);
      --coffee-bg-3: rgba(50, 83, 63, 0.09);
      --coffee-paper: #e5dbcf;
      --coffee-accent: #be8859;
      --coffee-olive: #6f856c;
      --coffee-smoke: #1b1918;
    """,
}


def inject_page_theme_variant(variant: str = "default") -> None:
    vars_css = _PAGE_THEME_VARIANTS.get(variant, _PAGE_THEME_VARIANTS["default"])
    st.markdown(
        f"""
        <style>
        :root {{
          {vars_css}
        }}
        body, .stApp {{
          background:
            radial-gradient(1200px 430px at 8% -8%, var(--coffee-bg-1) 0%, transparent 60%),
            radial-gradient(900px 360px at 88% 6%, var(--coffee-bg-3) 0%, transparent 62%),
            linear-gradient(180deg, rgba(17, 17, 17, 0.65) 0%, transparent 35%),
            #0e1014;
        }}
        section[data-testid="stMain"] {{
          background:
            radial-gradient(1000px 380px at 50% 102%, var(--coffee-bg-2) 0%, transparent 65%);
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def inject_region_page_css() -> None:
    st.markdown(
        """
        <style>
          :root {
            --coffee-panel-bg: rgba(26, 23, 20, 0.68);
            --coffee-panel-border: rgba(188, 146, 102, 0.18);
            --coffee-divider-left: rgba(99, 129, 92, 0.16);
            --coffee-divider-mid: rgba(194, 146, 95, 0.46);
            --coffee-divider-right: rgba(99, 85, 67, 0.16);
          }
          .block-container { padding-top: 1.1rem; padding-bottom: 2rem; max-width: 900px; }
          .s2-hero {
            border-left: 4px solid var(--s2-accent, #e86f51);
            padding: 0.65rem 0.95rem 0.62rem 1.12rem;
            margin-bottom: 1.25rem;
            border-radius: 12px;
            background:
              radial-gradient(560px 170px at 98% 10%, rgba(198, 149, 99, 0.09) 0%, transparent 68%),
              linear-gradient(180deg, rgba(43, 36, 31, 0.52) 0%, rgba(25, 23, 21, 0.45) 100%);
            box-shadow: inset 0 1px 0 rgba(255, 238, 213, 0.035), 0 8px 28px rgba(0, 0, 0, 0.16);
          }
          .s2-kicker {
            font-size: 0.82rem;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            color: #a49a8b;
            margin-bottom: 0.45rem;
            display: inline-flex;
            align-items: center;
            gap: 0.28rem;
            padding: 0.17rem 0.55rem;
            border-radius: 999px;
            border: 1px solid rgba(198, 157, 112, 0.28);
            background: rgba(58, 49, 41, 0.46);
          }
          .s2-hero h1 { font-size: 1.85rem; font-weight: 650; margin: 0 0 0.35rem 0; }
          .s2-lede { color: #c5cad3; font-size: 1.05rem; line-height: 1.55; margin: 0; }
          .s2-bridge {
            background: var(--coffee-panel-bg);
            border: 1px solid var(--coffee-panel-border);
            border-radius: 12px;
            padding: 0.9rem 1.1rem;
            margin: 0.5rem 0 1.5rem 0;
            box-shadow: inset 0 1px 0 rgba(255, 238, 213, 0.03), 0 6px 18px rgba(0, 0, 0, 0.12);
          }
          .s2-bridge p { margin: 0; color: #b8bec8; font-size: 0.98rem; line-height: 1.55; }
          .s2-section-title {
            font-size: 1.2rem;
            font-weight: 600;
            margin: 1.85rem 0 0.62rem 0;
            color: var(--coffee-paper, #eef1f5);
            letter-spacing: -0.01em;
            position: relative;
            padding-bottom: 0.32rem;
          }
          .s2-section-title::after {
            content: "";
            display: block;
            width: min(220px, 55%);
            height: 1px;
            margin-top: 0.4rem;
            border-radius: 999px;
            background: linear-gradient(
              90deg,
              var(--coffee-divider-left),
              var(--coffee-divider-mid) 48%,
              rgba(199, 154, 108, 0.18) 68%,
              transparent 100%
            );
          }
          .s2-section p, .s2-section li {
            color: #c5cad3;
            font-size: 0.98rem;
            line-height: 1.58;
          }
          .s2-section p { margin: 0 0 0.75rem 0; }
          .s2-muted { color: #8b93a0; font-size: 0.88rem; line-height: 1.45; }
          .s2-divider {
            height: 1px;
            margin: 1.7rem 0;
            border-radius: 999px;
            background: linear-gradient(
              90deg,
              transparent 0%,
              var(--coffee-divider-left) 14%,
              var(--coffee-divider-mid) 50%,
              var(--coffee-divider-right) 86%,
              transparent 100%
            );
            position: relative;
          }
          .s2-divider::after {
            content: "";
            position: absolute;
            left: 50%;
            top: -4px;
            width: 10px;
            height: 10px;
            border-radius: 999px;
            transform: translateX(-50%);
            background: radial-gradient(circle at 40% 36%, rgba(232, 200, 155, 0.82) 0%, rgba(154, 108, 68, 0.8) 62%, rgba(91, 68, 50, 0.72) 100%);
            box-shadow: 0 0 0 1px rgba(198, 154, 112, 0.22), 0 0 14px rgba(144, 98, 61, 0.22);
            opacity: 0.85;
          }
          .stPlotlyChart, .stPydeckChart {
            border: 1px solid rgba(168, 138, 106, 0.16);
            border-radius: 12px;
            padding: 0.32rem 0.26rem 0.2rem 0.26rem;
            background:
              radial-gradient(520px 120px at 8% -12%, rgba(118, 91, 66, 0.12) 0%, transparent 58%),
              rgba(20, 21, 23, 0.44);
            box-shadow: inset 0 1px 0 rgba(252, 232, 206, 0.02);
          }
          .stCaption {
            color: #9b95a0 !important;
          }
"""
        + MAIN_CHAPTER_FOOTER_CSS
        + """
        </style>
        """,
        unsafe_allow_html=True,
    )
    inject_sidebar_theme_css()


def region_hero(
    region_key: str,
    *,
    kicker: str,
    title_override: Optional[str] = None,
    lede: str,
) -> None:
    meta = REGION_META[region_key]
    title = title_override or meta["title"]
    accent = meta["accent"]
    st.markdown(
        f"""
        <style> :root {{ --s2-accent: {accent}; }} </style>
        <div class="s2-hero">
          <div class="s2-kicker">{meta["emoji"]} &nbsp; {kicker}</div>
          <h1>{title}</h1>
          <p class="s2-lede">{lede}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def map_bridge() -> None:
    """Concise prose connecting the home map to regional chapters."""
    st.markdown(MAP_BRIDGE_HTML, unsafe_allow_html=True)


def render_chapter_nav_links() -> None:
    """
    Shared chapter list for the sidebar. Call inside ``with st.sidebar`` (e.g. landing map controls)
    or use :func:`sidebar_navigation` for a full sidebar with only chapters.

    Appendix appears here only; it is intentionally omitted from bottom-of-page nav.
    """
    st.markdown(
        '<p class="sbar-section-label">Chapters</p>',
        unsafe_allow_html=True,
    )
    for path, label, icon in CHAPTER_NAV_ENTRIES:
        st.page_link(path, label=label, icon=icon)
    st.markdown(
        '<hr style="border:none;border-top:1px solid rgba(148,163,184,0.18);margin:0.85rem 0 0.65rem 0;">',
        unsafe_allow_html=True,
    )
    apath, alabel, aicon = APPENDIX_SIDEBAR_LINK
    st.page_link(apath, label=alabel, icon=aicon)


def sidebar_navigation(active: str | None = None) -> None:
    """
    Chapter navigation for the full narrative arc (active is reserved for future highlight).

    active: optional slug such as ``compare``, ``conclusion``, ``americas`` (currently unused).
    """
    _ = active
    with st.sidebar:
        render_chapter_nav_links()


def sidebar_chapters(current_region: str) -> None:
    """Backward-compatible alias for regional pages (delegates to shared sidebar)."""
    slug = {
        "Americas": "americas",
        "Africa": "africa",
        "Asia-Pacific": "asia_pacific",
    }.get(current_region, "home")
    sidebar_navigation(slug)


def render_chapter_footer_nav() -> None:
    """Horizontal chapter links + divider (landing + chapter footers)."""
    st.divider()
    # Equal-width columns so Streamlit column gaps are uniform (weighted cols looked uneven).
    cols = st.columns(6, gap="xxsmall")
    for col, (path, label, icon) in zip(cols, CHAPTER_NAV_ENTRIES):
        with col:
            st.page_link(path, label=label, icon=icon)


def chapter_footer_full_arc() -> None:
    """Bottom navigation mirroring the sidebar chapter list."""
    render_chapter_footer_nav()


def section_title(text: str) -> None:
    st.markdown(f'<div class="s2-section-title">{text}</div>', unsafe_allow_html=True)


def section_divider() -> None:
    st.markdown('<div class="s2-divider"></div>', unsafe_allow_html=True)


def prose_block(body: str, *, muted: bool = False) -> None:
    cls = "s2-muted" if muted else "s2-section"
    st.markdown(f'<div class="{cls}"><p>{body}</p></div>', unsafe_allow_html=True)
