import streamlit as st
import pandas as pd
from datetime import date

from ui.log_food import render_log_food
from ui.add_food import render_add_food

from analytics.totals import (
    get_daily_totals_for_date,
    get_detailed_logs_for_date,
    get_weekly_totals,
)


def render_dashboard():
    st.header("Dashboard")

    # ===============================
    # TOP ACTION BUTTONS (BLUE, 1 ROW)
    # ===============================
    col1, col2 = st.columns(2)

    if "dashboard_view" not in st.session_state:
        st.session_state.dashboard_view = None

    with col1:
        if st.button("Add Meal", type="primary", use_container_width=True):
            st.session_state.dashboard_view = "log_food"

    with col2:
        if st.button("Add New Details", type="primary", use_container_width=True):
            st.session_state.dashboard_view = "add_food"

    st.divider()

    # ===============================
    # ACTION SCREENS (FORMS)
    # ===============================
    if st.session_state.dashboard_view == "log_food":
        render_log_food()
        return

    if st.session_state.dashboard_view == "add_food":
        render_add_food()
        return

    # ===============================
    # DATE PICKER
    # ===============================
    selected_date = st.date_input(
        "Select date",
        value=date.today()
    )

    # ===============================
    # DAILY SUMMARY
    # ===============================
    st.subheader("Daily Summary")

    daily_df = get_daily_totals_for_date(selected_date)

    if daily_df.empty:
        st.info("No data for this date.")
    else:
        st.dataframe(
            daily_df.drop(columns=["date"]),
            use_container_width=True
        )

    # ===============================
    # DAILY DETAILS
    # ===============================
    st.subheader("Detailed Logs")

    detailed_df = get_detailed_logs_for_date(selected_date)

    if detailed_df.empty:
        st.info("No food logged for this date.")
    else:
        st.dataframe(
            detailed_df.drop(columns=["date"]),
            use_container_width=True
        )

    # ===============================
    # WEEKLY OVERVIEW
    # ===============================
    st.subheader("Weekly Overview (Last 7 Days)")

    weekly_df = get_weekly_totals(date.today())

    if weekly_df.empty:
        st.info("No data in the last 7 days.")
        return

    st.dataframe(
        weekly_df,
        use_container_width=True
    )

    st.line_chart(
        weekly_df.set_index("date")[["calories", "protein", "carbs", "fat"]]
    )
