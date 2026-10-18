"""Shared active-date state.

The date is correct by default almost every time, so it reads as a line of
text rather than a picker. Changing it costs one tap; leaving it costs none.
"""

from datetime import date

import streamlit as st

DATE_KEY = "active_date"
PICKER_KEY = "show_date_picker"


def get_active_date():
    if DATE_KEY not in st.session_state:
        st.session_state[DATE_KEY] = date.today()
    return st.session_state[DATE_KEY]


def set_active_date(value):
    st.session_state[DATE_KEY] = value


def render_date_bar():
    today = date.today()
    active = get_active_date()
    is_today = active == today

    col1, col2 = st.columns([4, 1])

    label = f"Today · {active:%a %d %b}" if is_today else f"{active:%a %d %b}"
    col1.markdown(f"#### {label}")

    if is_today:
        if col2.button("Change", use_container_width=True):
            st.session_state[PICKER_KEY] = not st.session_state.get(PICKER_KEY, False)
    else:
        if col2.button("Today", type="primary", use_container_width=True):
            set_active_date(today)
            st.session_state[PICKER_KEY] = False
            st.rerun()

    if st.session_state.get(PICKER_KEY):
        picked = st.date_input(
            "Date",
            value=active,
            label_visibility="collapsed",
            key="date_bar_picker",
        )
        if picked != active:
            set_active_date(picked)
            st.session_state[PICKER_KEY] = False
            st.rerun()

    return st.session_state[DATE_KEY]
