"""Ordering for the quick-log grid.

The grid's CONTENTS are whatever the user picked (services.picks) -- nothing
is suggested on its own. This module only decides the ORDER within those
picks, by how often each is logged, and supplies the amount you last used so
the dialog opens pre-filled.

Score is frequency with exponential recency decay: logged today counts 1.0,
logged a fortnight ago counts 0.5. A pick you have never logged scores 0 and
sorts last, but still appears -- you asked for it.
"""

from collections import defaultdict
from datetime import date, timedelta

import pandas as pd

from db.queries import get_recent_logs
from services.foods import list_foods
from services.picks import list_picks
from services.recipes import sorted_items

LOOKBACK_DAYS = 60
HALF_LIFE_DAYS = 14


def _weight(days_ago):
    return 0.5 ** (days_ago / HALF_LIFE_DAYS)


def _as_quantity(grams, food):
    """Express grams in the food's own unit where it has one."""
    grams_per_unit = food.get("grams_per_unit")
    if grams_per_unit:
        return round(float(grams) / float(grams_per_unit), 2), False
    return round(float(grams), 1), True


def build_suggestions(today=None, lookback_days=LOOKBACK_DAYS, limit=None):
    """Returns {"items": [...the user's picks, best-first...],
                "last_amounts": {food_id: {quantity, in_grams, last_date}}}"""
    today = today or date.today()
    cutoff = today - timedelta(days=lookback_days)

    picks = list_picks()
    logs = get_recent_logs(cutoff).data or []

    food_score = defaultdict(float)
    food_times = defaultdict(int)
    recipe_dates = defaultdict(set)
    recipe_rows = defaultdict(list)
    last_seen = {}

    for log in logs:
        try:
            log_date = pd.to_datetime(log["date"]).date()
        except (TypeError, ValueError):
            continue

        days_ago = (today - log_date).days
        if days_ago < 0:
            continue

        food_id = log.get("food_id")
        recipe_id = log.get("recipe_id")

        if food_id is not None and (
            food_id not in last_seen or log_date > last_seen[food_id][0]
        ):
            last_seen[food_id] = (log_date, log["grams"])

        if recipe_id is not None:
            # A meal writes one row per ingredient; score it once per day.
            recipe_dates[recipe_id].add(log_date)
            recipe_rows[recipe_id].append((log_date, log))
        elif food_id is not None:
            food_score[food_id] += _weight(days_ago)
            food_times[food_id] += 1

    items = []

    for pick in picks:
        if pick["kind"] == "food":
            food = pick["food"]
            food_id = pick["target_id"]
            previous = last_seen.get(food_id)

            if previous:
                quantity, in_grams = _as_quantity(previous[1], food)
            elif food.get("grams_per_unit"):
                quantity, in_grams = 1.0, False
            else:
                quantity, in_grams = 100.0, True

            items.append({
                "kind": "food",
                "id": food_id,
                "pick_id": pick["pick_id"],
                "label": food["name"],
                "unit_name": "g" if in_grams else (food.get("unit_name") or "unit"),
                "default_quantity": quantity,
                "in_grams": in_grams,
                "times": food_times.get(food_id, 0),
                "last_date": previous[0] if previous else None,
                "score": food_score.get(food_id, 0.0),
                "food": food,
                "overrides": None,
            })
        else:
            recipe = pick["recipe"]
            recipe_id = pick["target_id"]
            dates = recipe_dates.get(recipe_id, set())
            score = sum(_weight((today - d).days) for d in dates)

            ingredients = sorted_items(recipe)
            overrides = {}
            headline = None

            grams_by_food = {}
            if dates:
                latest = max(dates)
                grams_by_food = {
                    log["food_id"]: log["grams"]
                    for log_date, log in recipe_rows[recipe_id] if log_date == latest
                }

            for item in ingredients:
                food = item["foods"]
                grams = grams_by_food.get(item["food_id"])
                if grams is None:
                    quantity = float(item["quantity"])
                else:
                    quantity, _ = _as_quantity(grams, food)
                overrides[item["id"]] = quantity
                # The headline is the ingredient the meal is named for: it is
                # what the tile shows, so only is_variable earns that spot.
                if headline is None and item.get("is_variable"):
                    headline = (quantity, food.get("unit_name") or "unit")

            items.append({
                "kind": "recipe",
                "id": recipe_id,
                "pick_id": pick["pick_id"],
                "label": recipe["name"],
                "unit_name": headline[1] if headline else "serving",
                "default_quantity": headline[0] if headline else 1.0,
                "in_grams": False,
                "times": len(dates),
                "last_date": max(dates) if dates else None,
                "score": score,
                "recipe": recipe,
                "overrides": overrides,
            })

    items.sort(key=lambda i: (-i["score"], i["label"]))
    if limit:
        items = items[:limit]

    # Expressed in each food's own unit, since that is how the form asks.
    all_foods = {f["id"]: f for f in list_foods()}
    last_amounts = {}
    for food_id, (last_date, grams) in last_seen.items():
        food = all_foods.get(food_id)
        if food is None:
            continue
        quantity, in_grams = _as_quantity(grams, food)
        last_amounts[food_id] = {
            "quantity": quantity,
            "in_grams": in_grams,
            "last_date": last_date,
        }

    return {"items": items, "last_amounts": last_amounts}
