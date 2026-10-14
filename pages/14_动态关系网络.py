"""Dynamic GDELT country event network."""
from pathlib import Path
import sys
import streamlit as st
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.presentation import apply_presentation
from src.gdelt_network import render_network_page
st.set_page_config(page_title="动态关系网络 · 北极观察", page_icon="◎", layout="wide")
apply_presentation("network")
render_network_page()
