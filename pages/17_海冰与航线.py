import streamlit as st

from src.presentation import apply_presentation
from src.seaice_views import render_seaice_page

st.set_page_config(page_title="海冰与航线 · 北极观察", page_icon="◎", layout="wide")
apply_presentation("support")
render_seaice_page()
