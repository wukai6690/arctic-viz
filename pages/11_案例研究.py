import streamlit as st
from src.presentation import apply_presentation
from src.case_views import render_cases
st.set_page_config(page_title='案例研究 · 北极观察',page_icon='◎',layout='wide')
apply_presentation('cases')
render_cases()
