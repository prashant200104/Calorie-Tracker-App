import json
import math

import streamlit as st

from db.nutrients import COLUMN, FOOD_ATTRIBUTES, GROUPS, KEYS_IN_GROUP, LABEL, UNIT
from services.foods import add_food


def _nutrient_inputs(keys, cols_per_row=3):
    """Render number inputs for `keys`; return {column: value} for ones set > 0.

    Left blank (0) means "not known" and is omitted so the column stays NULL,
    which keeps it distinguishable from a real measured zero.
    """
    values = {}
    for i in range(0, len(keys), cols_per_row):
        chunk = keys[i:i + cols_per_row]
        cols = st.columns(len(chunk))
        for col, key in zip(cols, chunk):
            val = col.number_input(
                f"{LABEL[key]} ({UNIT[key]})",
                min_value=0.0,
                value=0.0,
                step=0.1,
                format="%.3f",
                key=f"add_food_{key}",
            )
            if val > 0:
                values[COLUMN[key]] = val
    return values


def render_add_food():
    st.header("Add Food")
    st.caption(
        "All nutrition is entered **per 100 g**. Leave a field at 0 if you don't "
        "know it — it stays empty rather than being recorded as a measured zero."
    )

    name = st.text_input("Food name", placeholder="e.g. health_factory_whole_wheat_bread")

    # ---------------- serving unit ----------------
    st.subheader("Serving unit")
    st.caption("Lets you log this food by slice / egg / scoop / tbsp instead of weighing it.")
    ucol1, ucol2 = st.columns(2)
    unit_name = ucol1.text_input("Unit name", placeholder="slice, egg, scoop, tbsp")
    grams_per_unit = ucol2.number_input(
        "Grams per unit", min_value=0.0, value=0.0, step=0.5
    )

    # ---------------- nutrients ----------------
    values = {}
    food_attributes = {}
    amino_acids_json = ""
    for group in GROUPS:
        if group == "Macros":
            st.subheader("Macros")
            values.update(_nutrient_inputs(KEYS_IN_GROUP[group]))
        elif group == "Amino acids":
            with st.expander(f"{group} (optional)"):
                values.update(_nutrient_inputs(KEYS_IN_GROUP[group]))
                amino_acids_json = st.text_area(
                    "Full amino-acid profile (mg per 100 g, JSON)",
                    placeholder='{"leucine": 5603, "isoleucine": 3450}',
                    key="add_food_amino_acids_json",
                )
        else:
            with st.expander(f"{group} (optional)"):
                values.update(_nutrient_inputs(KEYS_IN_GROUP[group]))
                if group == "Other":
                    for key, (label, unit) in FOOD_ATTRIBUTES.items():
                        value = st.number_input(
                            f"{label} ({unit})",
                            min_value=0.0,
                            value=0.0,
                            step=1.0,
                            key=f"add_food_{key}",
                        )
                        if value > 0:
                            food_attributes[key] = value

    # ---------------- provenance ----------------
    with st.expander("Source & caveats (optional)"):
        source = st.text_input("Source", placeholder="Pack label / USDA FoodData Central / estimated")
        notes = st.text_area("Notes", placeholder="Label inconsistencies, estimation caveats, …")

    if st.button("Add food", type="primary"):
        if not name.strip():
            st.error("Food name is required")
            return

        food = {"name": name.strip().lower().replace(" ", "_")}
        food.update(values)
        food.update(food_attributes)

        if amino_acids_json.strip():
            try:
                amino_acids = json.loads(amino_acids_json)
            except json.JSONDecodeError as error:
                st.error(f"Amino-acid profile must be valid JSON: {error.msg}")
                return
            if not isinstance(amino_acids, dict) or any(
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or value < 0
                for value in amino_acids.values()
            ):
                st.error("Amino-acid profile must be a JSON object with non-negative numeric values.")
                return
            food["amino_acids_mg_per_100g"] = amino_acids

        if unit_name.strip() and grams_per_unit > 0:
            food["unit_name"] = unit_name.strip().lower()
            food["grams_per_unit"] = grams_per_unit
        elif unit_name.strip() or grams_per_unit > 0:
            st.error("Set both unit name and grams per unit, or neither")
            return

        if source.strip():
            food["source"] = source.strip()
        if notes.strip():
            food["notes"] = notes.strip()

        try:
            add_food(food)
            nutrient_count = len(values) + len(food_attributes)
            nutrient_count += int("amino_acids_mg_per_100g" in food)
            st.success(f"Added {food['name']} with {nutrient_count} nutrient values")
        except Exception as e:
            st.error(str(e))
