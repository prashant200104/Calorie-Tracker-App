"""Every read goes through here, and one call clears the lot.

Streamlit re-executes the whole script on every tap, so an uncached read is
a Supabase round-trip per interaction -- the app was making seven, twice of
them full-table. These wrappers hold a run's reads in memory; `clear()` runs
after each write so the next render sees fresh data.

TTL is a safety net for edits made from another device, not the mechanism:
correctness comes from clearing on write.
"""

import streamlit as st

from services.foods import list_foods
from services.logs import list_logs_between, list_logs_for_date
from services.picks import list_picks
from services.recipes import list_recipes, list_recipes_with_items
from services.suggestions import build_suggestions

TTL = 300  # seconds


@st.cache_data(ttl=TTL, show_spinner=False)
def logs_for_date(day):
    return list_logs_for_date(day)


@st.cache_data(ttl=TTL, show_spinner=False)
def logs_between(start_day, end_day):
    return list_logs_between(start_day, end_day)


@st.cache_data(ttl=TTL, show_spinner=False)
def recipes_with_items():
    return list_recipes_with_items()


@st.cache_data(ttl=TTL, show_spinner=False)
def recipes():
    return list_recipes()


@st.cache_data(ttl=TTL, show_spinner=False)
def foods():
    return list_foods()


@st.cache_data(ttl=TTL, show_spinner=False)
def picks():
    return list_picks()


@st.cache_data(ttl=TTL, show_spinner=False)
def suggestions(day, limit=None):
    return build_suggestions(today=day, limit=limit)


_CACHED = (
    logs_for_date, logs_between, recipes_with_items, recipes,
    foods, picks, suggestions,
)


def clear():
    """Call after ANY write. Cheap: it only drops the memo, nothing refetches."""
    for cached in _CACHED:
        cached.clear()
