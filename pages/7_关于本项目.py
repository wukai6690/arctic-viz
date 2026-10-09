"""关于研究 · source-linked research view."""
from pathlib import Path
import sys
import streamlit as st
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.presentation import apply_presentation
from src.support_views import render_about
st.set_page_config(page_title='关于研究 · 北极观察',page_icon='◎',layout='wide')
apply_presentation('support')
render_about()
