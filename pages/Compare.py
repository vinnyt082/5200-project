"""Cross-region comparison (Stage 3)."""

import streamlit as st

from app.config import streamlit_page_icon

st.set_page_config(
    page_title="Compare | From Origin to Cup",
    page_icon=streamlit_page_icon(),
    layout="wide",
    initial_sidebar_state="expanded",
)

from app.stage3.compare_page import render

render()
