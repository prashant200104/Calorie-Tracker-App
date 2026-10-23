from datetime import date

import streamlit as st

from services import cache
from services.logs import add_log
from services.recipes import item_grams, log_recipe, sorted_items
from ui.nutrition_preview import pretty, show_preview, unit_label, unit_step
from ui.quick_log import load_suggestions, refresh


def _last_amounts():
    try:
        return load_suggestions(date.today())["last_amounts"]
    except Exception:
        return {}


def show_notes(row):
    if row.get("source"):
        st.caption(f"**Source:** {row['source']}")
    if row.get("notes"):
        with st.expander("Caveats"):
            st.write(row["notes"])


def render_log_food(selected_date):
    recipes = cache.recipes_with_items()

    if recipes:
        tab = st.radio(
            "What are you logging?",
            ["Single food", "Meal"],
            horizontal=True,
            label_visibility="collapsed",
        )
    else:
        tab = "Single food"

    if tab == "Meal":
        render_meal(selected_date, recipes)
    else:
        render_single_food(selected_date)


# -------------------------------------------------------------------- meals
def render_meal(selected_date, recipes):
    recipe_map = {pretty(r["name"]): r for r in recipes}
    selected = st.selectbox("Meal", options=list(recipe_map.keys()))
    recipe = recipe_map[selected]

    if recipe.get("description"):
        st.caption(recipe["description"])

    items = sorted_items(recipe)
    if not items:
        st.warning(f"'{recipe['name']}' has no ingredients yet.")
        return

    last = _last_amounts()
    overrides = {}
    parts = []
    invalid = False

    for item in items:
        food = item["foods"]
        unit_text = "g" if item["unit"] == "g" else unit_label(food.get("unit_name"))

        previous = last.get(item["food_id"])
        default = (
            previous["quantity"]
            if previous and not previous["in_grams"]
            else float(item["quantity"])
        )
        quantity = st.number_input(
            f"{pretty(food['name'])} — {unit_text}s",
            min_value=0.0,
            value=float(default),
            step=1.0 if item["unit"] == "unit" else 10.0,
            key=f"recipe_item_{item['id']}",
        )
        overrides[item["id"]] = quantity

        if quantity <= 0:
            invalid = True
            continue

        try:
            grams = item_grams(item, quantity)
        except ValueError as e:
            st.error(str(e))
            invalid = True
            continue

        parts.append((food, grams))

    if parts:
        show_preview(parts)

    show_notes(recipe)

    if st.button(f"Log {pretty(recipe['name'])}", type="primary",
                 use_container_width=True, disabled=invalid):
        try:
            log_recipe(date=selected_date, recipe=recipe, overrides=overrides)
        except Exception as e:
            st.error(str(e))
            return
        refresh()
        st.toast(f"{pretty(recipe['name'])} logged", icon="✅")
        st.rerun()


# ------------------------------------------------------------- single food
def render_single_food(selected_date):
    foods = cache.foods()
    if not foods:
        st.warning("No foods found. Run db/supabase_setup.sql first.")
        return

    last = _last_amounts()

    # Most-recently-logged foods float to the top of the list.
    def rank(food):
        previous = last.get(food["id"])
        return (0, -previous["last_date"].toordinal()) if previous else (1, 0)

    ordered = sorted(foods, key=lambda f: (rank(f), f["name"]))

    food_map = {}
    for food in ordered:
        label = pretty(food["name"])
        if food.get("grams_per_unit"):
            label += (
                f"  ·  1 {unit_label(food.get('unit_name'))}"
                f" = {food['grams_per_unit']:g} g"
            )
        food_map[label] = food

    selected_label = st.selectbox("Food", options=list(food_map.keys()))
    food = food_map[selected_label]

    grams_per_unit = food.get("grams_per_unit")
    has_unit = grams_per_unit is not None
    unit_text = unit_label(food.get("unit_name"))

    previous = last.get(food["id"])

    # Foods with a unit default to it; weighing is the opt-in.
    by_weight = not has_unit
    if has_unit:
        by_weight = st.toggle(
            "Log by weight instead",
            value=bool(previous and previous["in_grams"]),
            key=f"by_weight_{food['id']}",
        )

    if by_weight:
        default = (
            previous["quantity"]
            if previous and previous["in_grams"]
            else (float(grams_per_unit) if has_unit else 100.0)
        )
        amount = st.number_input(
            "Grams", min_value=0.0, value=float(default), step=10.0,
            key=f"grams_{food['id']}",
        )
        grams, quantity = amount, None
    else:
        default = (
            previous["quantity"]
            if previous and not previous["in_grams"]
            else 1.0
        )
        amount = st.number_input(
            f"{unit_text.capitalize()}s  (1 = {grams_per_unit:g} g)",
            min_value=0.0, value=float(default), step=unit_step(grams_per_unit),
            key=f"units_{food['id']}_{unit_text}",
        )
        quantity, grams = amount, None

    if previous:
        st.caption(f"Last logged {previous['last_date']:%d %b}.")

    effective_grams = grams if grams else (
        quantity * float(grams_per_unit) if quantity else None
    )

    if effective_grams:
        show_preview([(food, effective_grams)])
        if quantity:
            st.caption(f"= {effective_grams:g} g")

    show_notes(food)

    if st.button("Log it", type="primary", use_container_width=True):
        if not effective_grams:
            st.error("Amount must be greater than 0")
            return
        try:
            add_log(date=selected_date, food=food, quantity=quantity, grams=grams)
        except Exception as e:
            st.error(str(e))
            return
        refresh()
        st.toast(f"Logged {effective_grams:g} g {pretty(food['name'])}", icon="✅")
        st.rerun()
