import streamlit as st
from src.presentation import apply_presentation
from src.source_library import render_library

st.set_page_config(page_title='站内资料 · 北极观察',page_icon='◎',layout='wide')
apply_presentation('reading')
render_library()
