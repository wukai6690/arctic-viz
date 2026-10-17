"""Standalone Arctic technology patent database."""
import streamlit as st
from src.presentation import apply_presentation
from src.patent_views import render_patent_database

st.set_page_config(page_title="专利数据库 · 北极观察", page_icon="◎", layout="wide")
apply_presentation("technology")
render_patent_database()
