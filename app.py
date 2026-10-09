"""Research overview of the original Streamlit platform."""
import streamlit as st
from src.presentation import apply_presentation
from src.home_views import render_home
st.set_page_config(page_title='北极观察 · 研究总览',page_icon='◎',layout='wide',initial_sidebar_state='expanded')
apply_presentation('home')
render_home()
