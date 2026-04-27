"""Americas regional storytelling (Stage 2)."""

import streamlit as st

from app.config import streamlit_page_icon

st.set_page_config(
    page_title="Americas | From Origin to Cup",
    page_icon=streamlit_page_icon(),
    layout="wide",
    initial_sidebar_state="expanded",
)

from app.stage2.americas_page import render

render()
