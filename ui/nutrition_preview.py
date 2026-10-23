"""Shared macro preview, so the grid dialog and the full form agree."""

import re

import streamlit as st

from analytics.totals import sum_parts
from db.nutrients import LABEL, UNIT

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


def unit_step(grams_per_unit):
    """How far one tap of the stepper moves.

    Whole units for an egg or a slice. A litre-sized unit moves by a tenth,
    so 1.2 L is two taps off 1 L rather than an amount you cannot reach.
    """
    try:
        grams = float(grams_per_unit or 0)
    except (TypeError, ValueError):
        return 1.0
    return 0.1 if grams >= 500 else 1.0


def show_preview(parts, compact=False):
    totals = sum_parts(parts, PREVIEW_KEYS)

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
