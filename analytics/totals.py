from datetime import timedelta

import pandas as pd

from db.nutrients import COLUMN, KEYS
from db.queries import get_logs_with_foods


def _nutrient_values(food, factor):
    """Scale every registry nutrient from per-100g to the logged amount.

    A missing/NULL column contributes 0 so sums stay numeric; use the foods
    table itself if you need to tell "not known" apart from a real zero.
    """
    return {key: factor * (food.get(COLUMN[key]) or 0) for key in KEYS}


def _log_rows(include_food_name):
    response = get_logs_with_foods()
    data = response.data

    if not data:
        return []

    rows = []

    for log in data:
        food = log.get("foods")
        if not food:
            continue

        date_val = log.get("date")
        if not date_val:
            continue
        date_val = pd.to_datetime(date_val).date()

        try:
            grams = float(log.get("grams", 0))
        except (TypeError, ValueError):
            continue

        if grams <= 0:
            continue

        row = {"date": date_val}
        if include_food_name:
            row["food"] = food["name"]
            row["grams"] = grams
        row.update(_nutrient_values(food, grams / 100.0))
        rows.append(row)

    return rows


def get_daily_totals():
    rows = _log_rows(include_food_name=False)
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    return (
        df.groupby("date", as_index=False)
          .sum()
          .sort_values("date")
    )


def get_detailed_logs():
    rows = _log_rows(include_food_name=True)
    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(rows).sort_values(["date", "food"])


def get_daily_totals_for_date(target_date):
    df = get_daily_totals()
    if df.empty:
        return df
    return df[df["date"] == target_date]


def get_detailed_logs_for_date(target_date):
    df = get_detailed_logs()
    if df.empty:
        return df
    return df[df["date"] == target_date]


def get_weekly_totals(end_date):
    df = get_daily_totals()
    if df.empty:
        return df

    start_date = end_date - timedelta(days=6)
    return df[(df["date"] >= start_date) & (df["date"] <= end_date)]
