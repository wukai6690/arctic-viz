"""北极地图 · source-linked research view."""
from pathlib import Path
import sys
import streamlit as st
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.presentation import apply_presentation
from src.atlas_views import prepare_map_click, render_atlas
st.set_page_config(page_title='北极地图 · 北极观察',page_icon='◎',layout='wide')
apply_presentation('focused')
prepare_map_click()
render_atlas()
