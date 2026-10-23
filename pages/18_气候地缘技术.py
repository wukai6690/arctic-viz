"""Climate–geopolitics–technology coupling explorer."""
import streamlit as st

from src.coupling_views import render_coupling_page
from src.presentation import apply_presentation

st.set_page_config(page_title="气候—地缘—技术 · 北极观察", page_icon="◎", layout="wide")
apply_presentation("coupling")
render_coupling_page()
