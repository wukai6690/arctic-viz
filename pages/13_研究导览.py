import streamlit as st
from src.presentation import apply_presentation
from src.research_tour import render_tour
st.set_page_config(page_title='研究导览 · 北极观察',page_icon='◎',layout='wide')
apply_presentation('tour')
render_tour()
