"""Unified Arctic event search, candidate library and source reading."""
import streamlit as st
from src.presentation import apply_presentation
from src.event_search import render_event_search_center

st.set_page_config(page_title="事件检索 · 北极观察", page_icon="🔎", layout="wide")
apply_presentation("focused")
render_event_search_center()
