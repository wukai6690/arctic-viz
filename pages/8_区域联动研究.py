"""Regional observations, case evidence and coverage in one study scope."""
from pathlib import Path
import sys
import streamlit as st
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.presentation import apply_presentation
from src.study_views import render_study
st.set_page_config(page_title='区域联动 · 北极观察',page_icon='◎',layout='wide')
apply_presentation('focused')
render_study()
