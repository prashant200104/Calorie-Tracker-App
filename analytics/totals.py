"""Nutrient sums over logged rows.

These used to pull EVERY log ever written (`get_logs_with_foods`) and filter
in pandas -- twice per render, since the day totals and the week chart each
did their own scan. Now a caller fetches the rows it needs once, date-bounded
and cached, and these functions only do arithmetic.
"""

from datetime import timedelta

import pandas as pd

from db.nutrients import COLUMN, KEYS
from services.cache import logs_between


def scale(food, grams, keys=KEYS):
    """Scale a per-100g food row to the amount actually eaten.

    A missing/NULL column contributes 0 so sums stay numeric; use the foods
    table itself if you need to tell "not known" apart from a real zero.
    """
    factor = grams / 100.0
    return {key: factor * (food.get(COLUMN[key]) or 0) for key in keys}


def sum_parts(parts, keys=KEYS):
    """parts: [(food, grams)] -> one total per key."""
    totals = {key: 0.0 for key in keys}
    for food, grams in parts:
        for key, value in scale(food, grams, keys).items():
            totals[key] += value
    return totals


def _usable(log):
    """(date, grams, food) for a log row, or None if it can't be counted."""
    food = log.get("foods")
    date_val = log.get("date")
    if not food or not date_val:
        return None

    try:
        grams = float(log.get("grams", 0))
    except (TypeError, ValueError):
        return None

    if grams <= 0:
        return None

    return pd.to_datetime(date_val).date(), grams, food


def totals_for_rows(rows):
    """Sum one day's (or any set of) log rows: {nutrient key: amount}.

    Returns {} for nothing logged, so callers can test it directly.
    """
    totals = {key: 0.0 for key in KEYS}
    counted = 0

    for log in rows or []:
        usable = _usable(log)
        if usable is None:
            continue
        _date, grams, food = usable
        for key, value in scale(food, grams).items():
            totals[key] += value
        counted += 1

    return totals if counted else {}


def daily_totals_frame(rows):
    """One row per logged day, every nutrient summed -- for the week charts."""
    records = []
    for log in rows or []:
        usable = _usable(log)
        if usable is None:
            continue
        date_val, grams, food = usable
        record = {"date": date_val}
        record.update(scale(food, grams))
        records.append(record)

    if not records:
        return pd.DataFrame()

    return (
        pd.DataFrame(records)
          .groupby("date", as_index=False)
          .sum()
          .sort_values("date")
    )


def get_weekly_totals(end_date, days=7):
    """Daily totals for the `days`-day window ending on end_date."""
    start_date = end_date - timedelta(days=days - 1)
    return daily_totals_frame(logs_between(start_date, end_date))
