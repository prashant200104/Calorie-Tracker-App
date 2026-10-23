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


@st.fragment
def render_date_bar():
    """A fragment: opening or closing the picker reruns this bar alone.
    Actually changing the date reruns the app, because the whole screen is
    about that day."""
    today = date.today()
    active = get_active_date()
    is_today = active == today

    label = f"Today · {active:%a %d %b}" if is_today else f"{active:%a %d %b}"
    if st.button(
        label,
        use_container_width=True,
        key="date_bar_label",
    ):
        st.session_state[PICKER_KEY] = not st.session_state.get(PICKER_KEY, False)

    if not is_today:
        if st.button("Today", type="primary", use_container_width=True):
            set_active_date(today)
            st.session_state[PICKER_KEY] = False
            st.rerun(scope="app")

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
            st.rerun(scope="app")
