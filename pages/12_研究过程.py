import streamlit as st
from src.presentation import apply_presentation
from src.research_process import render_process
st.set_page_config(page_title='研究过程 · 北极观察',page_icon='◎',layout='wide')
apply_presentation('process')
render_process()
