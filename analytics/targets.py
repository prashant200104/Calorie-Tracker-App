"""Load personal targets and compare them with a day's logged food."""

import json
import math
from functools import lru_cache
from pathlib import Path

from db.nutrients import COLUMN

TARGETS_PATH = Path(__file__).resolve().parents[1] / "config" / "daily_targets.json"
VALID_MODES = {"goal", "limit", "zero", "average_limit"}

# Water is logged as a food, so it is stored in GRAMS like everything else
# (1 ml ~ 1 g). What it is shown in is whatever unit the target declares, so
# switching between litres and millilitres is a config change, not a code one.
WATER_PER_UNIT = {
    "ml": 1.0, "millilitre": 1.0, "milliliter": 1.0,
    "l": 1000.0, "litre": 1000.0, "liter": 1000.0,
    "litres": 1000.0, "liters": 1000.0,
}


def water_grams_per_unit(target):
    return WATER_PER_UNIT.get(str(target.get("unit", "ml")).strip().lower(), 1.0)


@lru_cache(maxsize=1)
def load_daily_targets():
    data = json.loads(TARGETS_PATH.read_text(encoding="utf-8"))
    targets_by_key = {target["key"]: target for target in data["targets"]}
    display_groups = data["display_groups"]
    ordered_keys = [key for group in display_groups for key in group["keys"]]
    if len(ordered_keys) != len(set(ordered_keys)):
        raise ValueError("Each target must appear in only one display group")
    if set(ordered_keys) != set(targets_by_key):
        raise ValueError("Display groups must include every target exactly once")

    targets = []
    for group in display_groups:
        for key in group["keys"]:
            target = {**targets_by_key[key], "group": group["label"]}
            targets.append(target)

    for target in targets:
        key = target["key"]
        if target["mode"] not in VALID_MODES:
            raise ValueError(f"Unsupported target mode: {target['mode']}")
        if key not in {"glycemic_index", "water"} and key not in COLUMN:
            raise ValueError(f"Unknown nutrient target: {key}")
    return targets


def _number(value):
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _status(target, intake, coverage, has_food):
    if not has_food:
        return "No food logged"
    if intake is None:
        return "No usable nutrition data"

    complete = coverage >= 1.0 - 1e-9
    mode = target["mode"]
    value = target["value"]

    if mode == "goal":
        if intake >= value:
            return "Covered" if complete else "Covered so far; data incomplete"
        return "Below target" if complete else "Data incomplete"

    if mode == "zero":
        if intake <= 0:
            return "Target met" if complete else "Target met so far; data incomplete"
        return "Trans fat logged" if complete else "Trans fat logged; data incomplete"

    if intake < value:
        return "Within limit" if complete else "Data incomplete"
    if intake == value:
        return "At limit" if complete else "At limit; data incomplete"
    return "Over limit" if complete else "Over limit; data incomplete"


def compare_daily_targets(log_rows, targets=None):
    """Return target, consumed amount, data coverage, and status for each target.

    Coverage is weighted by logged food grams. Glycemic index is averaged by
    consumed carbohydrate grams and requires both GI and carbohydrate data.
    Water is counted from a food row named "water"; logged grams are read as
    millilitres (1 g/ml) and then converted into the unit its target declares.
    """
    targets = load_daily_targets() if targets is None else targets
    totals = {target["key"]: 0.0 for target in targets}
    known_grams = {target["key"]: 0.0 for target in targets}
    gi_weighted_sum = 0.0
    gi_carb_weight = 0.0
    total_logged_grams = 0.0

    for row in log_rows:
        food = row.get("foods") or {}
        grams = _number(row.get("grams"))
        if grams is None or grams <= 0:
            continue

        total_logged_grams += grams
        factor = grams / 100.0

        for target in targets:
            key = target["key"]
            if key == "water":
                if str(food.get("name", "")).strip().lower() == "water":
                    totals[key] += grams
                    known_grams[key] += grams
                continue
            if key == "glycemic_index":
                glycemic_index = _number(food.get("glycemic_index"))
                carbohydrates = _number(food.get(COLUMN["carbs"]))
                if glycemic_index is None or carbohydrates is None:
                    continue
                known_grams[key] += grams
                carb_grams = max(0.0, carbohydrates * factor)
                if carb_grams:
                    gi_weighted_sum += glycemic_index * carb_grams
                    gi_carb_weight += carb_grams
                continue

            amount_per_100g = _number(food.get(COLUMN[key]))
            if amount_per_100g is None:
                continue
            totals[key] += amount_per_100g * factor
            known_grams[key] += grams

    results = []
    for target in targets:
        key = target["key"]
        if key == "glycemic_index":
            intake = gi_weighted_sum / gi_carb_weight if gi_carb_weight else None
        elif key == "water":
            intake = (
                totals[key] / water_grams_per_unit(target)
                if known_grams[key] else None
            )
        else:
            intake = totals[key] if known_grams[key] else None
        coverage_denominator = (
            known_grams[key] if key == "water" else total_logged_grams
        )
        coverage = (
            known_grams[key] / coverage_denominator
            if coverage_denominator else 0.0
        )
        results.append({
            **target,
            "intake": intake,
            "coverage": coverage,
            "status": _status(target, intake, coverage, total_logged_grams > 0),
        })

    return results
