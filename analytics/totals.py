import pandas as pd
from db.queries import get_logs_with_foods


def get_daily_totals():
    response = get_logs_with_foods()
    data = response.data

    if not data:
        return pd.DataFrame()

    rows = []

    for log in data:
        food = log.get("foods")
        if not food:
            continue

        # --- date ---
        date_val = log.get("date")
        if not date_val:
            continue
        date_val = pd.to_datetime(date_val).date()

        # --- grams ---
        try:
            grams = float(log.get("grams", 0))
        except (TypeError, ValueError):
            continue

        if grams <= 0:
            continue

        factor = grams / 100.0

        rows.append({
            "date": date_val,
            "calories": factor * food["calories_per_100g"],
            "protein": factor * food["protein_per_100g"],
            "fiber": factor * (food["fiber_per_100g"] or 0),
            "carbs": factor * food["carbohydrates_per_100g"],
            "fat": factor * food["fat_per_100g"],
            "bad_fat": factor * (food["bad_fat_per_100g"] or 0),
            "sugar": factor * (food["sugar_per_100g"] or 0),
        })

    df = pd.DataFrame(rows)

    if df.empty:
        return df

    return (
        df.groupby("date", as_index=False)
          .sum()
          .sort_values("date")
    )


def get_detailed_logs():
    response = get_logs_with_foods()
    data = response.data

    if not data:
        return pd.DataFrame()

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

        factor = grams / 100.0

        rows.append({
            "date": date_val,
            "food": food["name"],  # ✅ FOOD NAME SHOWN
            "grams": grams,
            "calories": factor * food["calories_per_100g"],
            "protein": factor * food["protein_per_100g"],
            "fiber": factor * (food["fiber_per_100g"] or 0),
            "carbs": factor * food["carbohydrates_per_100g"],
            "fat": factor * food["fat_per_100g"],
            "bad_fat": factor * (food["bad_fat_per_100g"] or 0),
            "sugar": factor * (food["sugar_per_100g"] or 0),
        })

    return pd.DataFrame(rows).sort_values(["date", "food"])

from datetime import date, timedelta

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
