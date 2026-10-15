"""Standalone GDELT event search and filtered country network."""
import streamlit as st
from src.presentation import apply_presentation
from src.gdelt_network import render_search_page

st.set_page_config(page_title="事件检索 · 北极观察", page_icon="🔎", layout="wide")
apply_presentation("network")
render_search_page()
