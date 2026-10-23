"""Standalone GDELT event search and filtered country network."""
import streamlit as st
from src.presentation import apply_presentation
from src.gdelt_network import render_search_page
from src.gdelt_bulk import render_bulk_candidates

st.set_page_config(page_title="事件检索 · 北极观察", page_icon="🔎", layout="wide")
apply_presentation("network")
search_tab, bulk_tab = st.tabs(["事件检索与来源阅读", "大规模新闻候选库"])
with search_tab:
    render_search_page()
with bulk_tab:
    render_bulk_candidates()
