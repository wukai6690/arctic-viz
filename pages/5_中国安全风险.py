"""研究发现 · source-linked research view."""
from pathlib import Path
import sys
import streamlit as st
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.presentation import apply_presentation
from src.research_views import render_findings
st.set_page_config(page_title='研究发现 · 北极观察',page_icon='◎',layout='wide')
apply_presentation('focused')
render_findings()
