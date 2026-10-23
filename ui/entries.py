"""What I ate: a list of rows inside one dropdown.

A meal is ONE row. The ingredient rows behind it serve the nutrient totals
and are never shown. Tapping a row opens a popup shaped to what it is --
"how many eggs?" for a meal, its own unit for a single food -- holding the
only two controls that matter: change the amount, or delete it.
"""

from collections import defaultdict

import streamlit as st

from db.nutrients import COLUMN, GROUPS, KEYS, KEYS_IN_GROUP
from services.logs import remove_log, set_log_grams
from services.recipes import delete_meal, meal_quantities, sorted_items, update_meal
from ui.nutrition_preview import pretty, unit_label
from ui.quick_log import refresh
from ui.theme import empty, nutrient_chips

TARGET_KEY = "entry_edit_target"


def _nutrients(parts):
    """parts: [(food, grams)] -> every registry nutrient, scaled and summed."""
    totals = {key: 0.0 for key in KEYS}
    for food, grams in parts:
        factor = grams / 100.0
        for key in KEYS:
            totals[key] += factor * (food.get(COLUMN[key]) or 0)
    return totals


def _food_amount(row):
    food = row.get("foods") or {}
    grams = float(row["grams"])
    per_unit = food.get("grams_per_unit")
    if per_unit:
        quantity = round(grams / float(per_unit), 2)
        return f"{quantity:g} {unit_label(food.get('unit_name'))}"
    return f"{grams:g} g"


def _meal_amount(recipe, rows):
    """'3 egg' -- the variable ingredients, which is what you actually chose."""
    quantities = meal_quantities(recipe, rows)
    parts = []
    for item in sorted_items(recipe):
        if not item.get("is_variable") or item["id"] not in quantities:
            continue
        unit = "g" if item["unit"] == "g" else (
            unit_label(item["foods"].get("unit_name"))
        )
        parts.append(f"{quantities[item['id']]:g} {unit}")
    return " + ".join(parts) if parts else "1 serving"


def build_entries(rows, recipes_by_id):
    usable = [r for r in rows if r.get("foods")]
    if not usable:
        return []

    meals = defaultdict(list)
    singles = []
    for row in usable:
        if row.get("recipe_id"):
            meals[row["recipe_id"]].append(row)
        else:
            singles.append(row)

    entries = []

    for recipe_id, meal_rows in meals.items():
        recipe = recipes_by_id.get(recipe_id)
        if recipe is None:
            # Recipe gone but its logs remain: fall back to plain food rows.
            singles.extend(meal_rows)
            continue
        parts = [(r["foods"], float(r["grams"])) for r in meal_rows]
        entries.append({
            "kind": "meal",
            "key": f"meal_{recipe_id}",
            "label": recipe["name"],
            "amount": _meal_amount(recipe, meal_rows),
            "nutrients": _nutrients(parts),
            "recipe": recipe,
            "rows": meal_rows,
        })

    for row in singles:
        food = row["foods"]
        entries.append({
            "kind": "food",
            "key": f"food_{row['id']}",
            "label": food["name"],
            "amount": _food_amount(row),
            "nutrients": _nutrients([(food, float(row["grams"]))]),
            "row": row,
        })

    entries.sort(key=lambda e: -e["nutrients"]["calories"])
    return entries


def render_entries(selected_date, entries):
    """Rows only -- the caller supplies the surrounding dropdown."""
    if not entries:
        empty("Nothing logged yet. Tap something above to start.")
        return

    for entry in entries:
        _render_row(entry)

    target = st.session_state.get(TARGET_KEY)
    if target is not None:
        _open_dialog(target, selected_date)


def _render_row(entry):
    n = entry["nutrients"]
    suffix = " · meal" if entry["kind"] == "meal" else ""
    label = (
        f"{pretty(entry['label'])}{suffix}\n\n"
        f"{entry['amount']}  ·  {n['calories']:.0f} kcal  ·  "
        f"{n['protein']:.0f}g protein"
    )
    if st.button(label, key=f"entry_{entry['key']}", use_container_width=True):
        st.session_state[TARGET_KEY] = entry


def _close():
    st.session_state.pop(TARGET_KEY, None)


def _apply(action, message):
    try:
        action()
    except Exception as e:
        st.error(str(e))
        return
    _close()
    refresh()
    st.toast(message, icon="✅")
    st.rerun(scope="app")


# ------------------------------------------------------------------- popup
def _open_dialog(entry, selected_date):
    suffix = " · meal" if entry["kind"] == "meal" else ""

    @st.dialog(f"{pretty(entry['label'])}{suffix}")
    def _dialog():
        nutrients = entry["nutrients"]
        nutrient_chips(nutrients, KEYS_IN_GROUP["Macros"])

        others = [k for g in GROUPS if g != "Macros" for k in KEYS_IN_GROUP[g]]
        present = [k for k in others if nutrients.get(k)]
        if present:
            with st.expander(f"All nutrients ({len(present)})"):
                for group in GROUPS:
                    if group == "Macros":
                        continue
                    keys = [k for k in KEYS_IN_GROUP[group] if nutrients.get(k)]
                    if keys:
                        st.caption(group)
                        nutrient_chips(nutrients, keys)

        if entry["kind"] == "meal":
            _meal_controls(entry, selected_date)
        else:
            _food_controls(entry)

    _dialog()


def _meal_controls(entry, selected_date):
    recipe = entry["recipe"]
    rows = entry["rows"]
    current = meal_quantities(recipe, rows)

    overrides = {}
    invalid = False

    for item in sorted_items(recipe):
        if not item.get("is_variable"):
            continue
        food = item["foods"]
        unit = "g" if item["unit"] == "g" else unit_label(food.get("unit_name"))
        quantity = st.number_input(
            f"How many {unit}s?",
            min_value=0.0,
            value=float(current.get(item["id"], item["quantity"])),
            step=1.0 if item["unit"] == "unit" else 10.0,
            key=f"edit_meal_{recipe['id']}_{item['id']}",
        )
        overrides[item["id"]] = quantity
        if quantity <= 0:
            invalid = True

    changed = any(
        abs(overrides.get(k, v) - v) > 1e-9 for k, v in current.items()
    )

    _actions(
        key=entry["key"],
        save_disabled=invalid or not changed,
        on_save=lambda: update_meal(selected_date, recipe, rows, overrides),
        on_delete=lambda: delete_meal(selected_date, recipe["id"]),
        label=pretty(recipe["name"]),
    )


def _food_controls(entry):
    row = entry["row"]
    food = row["foods"]
    current = float(row["grams"])
    per_unit = food.get("grams_per_unit")

    if per_unit:
        unit = unit_label(food.get("unit_name"))
        quantity = st.number_input(
            f"How many {unit}s?",
            min_value=0.0,
            value=round(current / float(per_unit), 2),
            step=1.0,
            key=f"edit_food_{row['id']}",
        )
        grams = quantity * float(per_unit)
        st.caption(f"= {grams:g} g")
    else:
        grams = st.number_input(
            "Grams", min_value=0.0, value=current, step=10.0,
            key=f"edit_food_g_{row['id']}",
        )

    _actions(
        key=entry["key"],
        save_disabled=not grams or int(round(grams)) == int(round(current)),
        on_save=lambda: set_log_grams(row["id"], grams),
        on_delete=lambda: remove_log(row["id"]),
        label=pretty(food["name"]),
    )


def _actions(key, save_disabled, on_save, on_delete, label):
    col1, col2 = st.columns([2, 1])

    if col1.button("Save", type="primary", use_container_width=True,
                   disabled=save_disabled, key=f"save_{key}"):
        _apply(on_save, f"Updated {label}")

    if col2.button("Delete", use_container_width=True, key=f"del_{key}"):
        _apply(on_delete, f"Deleted {label}")
