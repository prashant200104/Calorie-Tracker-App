import streamlit as st
from ui.dashboard import render_dashboard

st.set_page_config(
    page_title="Calorie Tracker",
    layout="centered"
)

# -------- Sidebar navigation (PAGE LEVEL) --------
# page = st.sidebar.selectbox(
#     "Page",
#     ["Dashboard"]
# )

# if page == "Dashboard":
render_dashboard()
