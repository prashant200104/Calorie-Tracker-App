import streamlit as st

from ui.dashboard import render_dashboard

st.set_page_config(
    page_title="Calorie Tracker",
    layout="centered",
)

render_dashboard()
