"""Shared macro preview, so the grid dialog and the full form agree."""

import re

import streamlit as st

from db.nutrients import COLUMN, LABEL, UNIT

PREVIEW_KEYS = ["calories", "protein", "carbs", "fat", "fiber"]


def pretty(name):
    return name.replace("_", " ").title()


# Unit names were typed as whole phrases -- "1 egg", "1 medium (peeled, 118g)"
# -- which read as "6 1 egg" and "How many 1 egg s?" once a count is put in
# front. The grams are already in grams_per_unit, so strip both.
_LEADING_ONE = re.compile(r"^\s*1\s+")
_TRAILING_PAREN = re.compile(r"\s*\([^)]*\)\s*$")


def unit_label(name, fallback="unit"):
    """'1 medium (peeled, 118g)' -> 'medium'."""
    if not name:
        return fallback
    cleaned = _TRAILING_PAREN.sub("", _LEADING_ONE.sub("", str(name))).strip()
    return cleaned or fallback


def totals_for(parts):
    """parts: [(food, grams)] -> {key: scaled total}"""
    totals = {key: 0.0 for key in PREVIEW_KEYS}
    for food, grams in parts:
        factor = grams / 100.0
        for key in PREVIEW_KEYS:
            totals[key] += factor * (food.get(COLUMN[key]) or 0)
    return totals


def show_preview(parts, compact=False):
    totals = totals_for(parts)

    if compact:
        st.caption(
            " · ".join(
                f"**{totals[k]:.0f}** {UNIT[k]} {LABEL[k].lower()}"
                for k in PREVIEW_KEYS
            )
        )
        return

    cols = st.columns(len(PREVIEW_KEYS))
    for col, key in zip(cols, PREVIEW_KEYS):
        col.metric(LABEL[key], f"{totals[key]:.1f} {UNIT[key]}")
