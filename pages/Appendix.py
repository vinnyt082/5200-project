"""Technical appendix — sources, supplementary views, disclosure."""

import streamlit as st

from app.config import streamlit_page_icon

st.set_page_config(
    page_title="Appendix | From Origin to Cup",
    page_icon=streamlit_page_icon(),
    layout="wide",
    initial_sidebar_state="expanded",
)

from app.stage3.appendix_page import render

render()
