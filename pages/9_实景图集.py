"""Searchable, attributed place and project photographs."""
from pathlib import Path
import sys
import streamlit as st
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.presentation import apply_presentation
from src.photo_views import render_photos
st.set_page_config(page_title='实景图集 · 北极观察',page_icon='◎',layout='wide')
apply_presentation('focused')
render_photos()
