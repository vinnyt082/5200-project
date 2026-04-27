"""Coffee-themed Streamlit sidebar chrome (CSS only)."""

from __future__ import annotations

import streamlit as st

# Green-bean wash (top) → espresso mid → roasted brown base. Cream/tan for nav only.
SIDEBAR_THEME_CSS = """
/* --- Sidebar shell: perceptible but restrained coffee tint --- */
section[data-testid="stSidebar"] {
  background:
    linear-gradient(
      180deg,
      rgba(72, 82, 68, 0.14) 0%,
      rgba(42, 44, 38, 0.06) 28%,
      transparent 52%
    ),
    linear-gradient(
      168deg,
      #1c2420 0%,
      #161512 46%,
      #1e1814 100%
    ) !important;
  border-right: 1px solid rgba(118, 98, 78, 0.28) !important;
  box-shadow: inset 0 1px 0 rgba(140, 158, 128, 0.09);
}
section[data-testid="stSidebar"] > div:first-child,
section[data-testid="stSidebar"] div.block-container {
  background: transparent !important;
}

/* Section labels: Chapters, Map */
p.sbar-section-label {
  font-size: 0.65rem !important;
  letter-spacing: 0.14em !important;
  text-transform: uppercase !important;
  font-weight: 600 !important;
  color: rgba(168, 162, 148, 0.55) !important;
  margin: 0.2rem 0 0.38rem 0.35rem !important;
  line-height: 1.25 !important;
}
p.sbar-section-label--spaced {
  margin-top: 0.85rem !important;
  margin-bottom: 0.28rem !important;
}

/* Legacy h4 chapter headers if any remain */
section[data-testid="stSidebar"] h4 {
  font-size: 0.65rem !important;
  letter-spacing: 0.14em !important;
  text-transform: uppercase !important;
  font-weight: 600 !important;
  color: rgba(168, 162, 148, 0.55) !important;
  margin: 0.2rem 0 0.38rem 0.35rem !important;
}

/* Chapter page links: keep Streamlit row layout (do not use display:block — it stacks icon over label) */
section[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] {
  display: flex !important;
  flex-direction: row !important;
  align-items: center !important;
  justify-content: flex-start !important;
  text-decoration: none !important;
  border-radius: 7px !important;
  padding: 0.26rem 0.5rem 0.26rem 0.42rem !important;
  margin: 0.04rem 0.62rem !important;
  color: #c9c0b2 !important;
  font-weight: 400 !important;
  font-size: 0.93rem !important;
  line-height: 1.35 !important;
  border: 1px solid transparent !important;
  gap: 0.45rem !important;
  transition: background 0.14s ease, color 0.14s ease, border-color 0.14s ease, box-shadow 0.14s ease !important;
}
section[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"]:hover {
  background: rgba(218, 202, 172, 0.06) !important;
  color: #ebe4d8 !important;
  border-color: rgba(168, 148, 118, 0.14) !important;
}
section[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"][aria-current="page"],
section[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"][data-active="true"] {
  background: rgba(210, 188, 152, 0.085) !important;
  border-color: rgba(188, 162, 128, 0.22) !important;
  color: #f0e8dc !important;
  box-shadow: inset 0 1px 0 rgba(255, 248, 235, 0.04);
}

/* Dividers */
section[data-testid="stSidebar"] hr {
  margin: 0.65rem 0.62rem !important;
  border: none !important;
  height: 1px !important;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(130, 108, 86, 0.32) 50%,
    transparent 100%
  ) !important;
}

/* Form controls */
section[data-testid="stSidebar"] label {
  font-size: 0.82rem !important;
  color: #9a9288 !important;
}
section[data-testid="stSidebar"] .stSelectbox,
section[data-testid="stSidebar"] .stToggle {
  margin-bottom: 0.4rem !important;
}
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
  font-size: 0.78rem !important;
  color: #6f6a62 !important;
}

/* Hide default multipage nav when config is off (belt-and-suspenders) */
section[data-testid="stSidebar"] ul[data-testid="stSidebarNav"] {
  display: none !important;
}
"""


def inject_sidebar_theme_css() -> None:
    st.markdown(f"<style>{SIDEBAR_THEME_CSS}</style>", unsafe_allow_html=True)
