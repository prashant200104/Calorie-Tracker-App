import json
import math

import streamlit as st

from db.nutrients import COLUMN, FOOD_ATTRIBUTES, GROUPS, KEYS_IN_GROUP, LABEL, UNIT
from services import cache
from services.food_import import ImportError_, parse, schema_prompt
from services.foods import add_food, save_food
from ui.clipboard import copy_button
from ui.nutrition_preview import pretty, show_preview
from ui.quick_log import refresh


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


@st.fragment
def render_add_food():
    st.header("Add Food")

    mode = st.segmented_control(
        "How to add",
        ["Import JSON", "By hand"],
        default="Import JSON",
        label_visibility="collapsed",
        key="add_food_mode",
    )
    if mode == "By hand":
        render_manual_form()
    else:
        render_json_import()


def _save_failed(error, name):
    """Postgres speaks in codes; say what to do about the one that bites here."""
    message = str(error)
    if "row-level security" in message or "42501" in message:
        st.error(
            f"**{pretty(name)} wasn't saved: the database won't accept new foods.**\n\n"
            "`foods` has row-level security on with a read-only policy, so the app "
            "can list foods but not add one. Run "
            "**db/migrations/010_foods_write_policy.sql** in the Supabase SQL editor, "
            "then try again — nothing about your JSON is wrong."
        )
    else:
        st.error(f"{pretty(name)}: {message}")


# ------------------------------------------------------------------ import
def render_json_import():
    """Fifty nutrient fields is a terrible thing to type, so: hand the schema
    to a model, paste back what it says."""
    st.caption(
        "Ask Claude or GPT for the numbers, paste the JSON back here. "
        "A name that already exists is **updated**, which is also how you fix "
        "a food whose values are wrong."
    )

    st.markdown("**1 · Copy the prompt**")
    food_name = st.text_input(
        "Which food?",
        placeholder="amul gold milk — optional, it just fills the name in",
        key="import_food_name",
    )
    copy_button(schema_prompt(food_name), "Copy prompt for Claude / GPT")
    with st.expander("See what gets copied"):
        st.code(schema_prompt(food_name), language="json")

    st.markdown("**2 · Paste the answer**")
    uploaded = st.file_uploader("Or upload a .json file", type=["json"], key="import_file")
    pasted = st.text_area(
        "JSON",
        height=180,
        placeholder='{"name": "amul_gold_milk", "calories_per_100g": 87, …}',
        label_visibility="collapsed",
        key="import_json",
    )

    blob = pasted
    if uploaded is not None:
        try:
            blob = uploaded.getvalue().decode("utf-8")
        except UnicodeDecodeError:
            st.error("That file isn't UTF-8 text.")
            return

    if not blob.strip():
        return

    try:
        rows, ignored = parse(blob)
    except ImportError_ as e:
        st.error(str(e))
        return

    if ignored:
        st.warning(
            "Ignored field(s) this database has no column for: "
            + ", ".join(f"`{key}`" for key in ignored)
        )

    try:
        existing = {food["name"] for food in cache.foods()}
    except Exception:
        existing = set()

    st.markdown("**3 · Check and save**")
    for row in rows:
        known = sum(
            1 for key, column in COLUMN.items() if row.get(column) is not None
        )
        verb = "updates existing" if row["name"] in existing else "new food"
        st.markdown(f"**{pretty(row['name'])}** — {verb} · {known} nutrient values")
        show_preview([(row, 100)], compact=True)
        if row.get("unit_name"):
            st.caption(f"1 {row['unit_name']} = {row['grams_per_unit']:g} g")
        if row.get("source"):
            st.caption(f"Source: {row['source']}")

    label = f"Save {len(rows)} food{'s' if len(rows) != 1 else ''}"
    if st.button(label, type="primary", use_container_width=True, key="import_save"):
        saved = []
        for row in rows:
            try:
                save_food(row)
            except Exception as e:
                _save_failed(e, row["name"])
                break
            saved.append(row["name"])
        if saved:
            refresh()
            st.success("Saved " + ", ".join(pretty(n) for n in saved))


# -------------------------------------------------------------------- form
def render_manual_form():
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
            # "0 = not known" is wrong for added sugar: for whole foods zero is
            # the true value, and leaving it NULL both loses the fact and holds
            # the Added sugar target at "data incomplete" forever.
            added_sugar_unknown = st.checkbox(
                "Added sugar not known",
                help=(
                    "Leave this off for whole foods — milk, fruit and nuts have "
                    "sugar but no ADDED sugar, and that zero is worth recording. "
                    "Tick it only for a packaged food whose label doesn't say."
                ),
                key="add_food_added_sugar_unknown",
            )
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

        added_column = COLUMN["added_sugar"]
        if added_column not in food and not added_sugar_unknown:
            food[added_column] = 0

        sugar_column = COLUMN["sugar"]
        if food.get(added_column) and food.get(added_column) > food.get(sugar_column, 0):
            st.error("Added sugar can't be more than total sugar.")
            return
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
        except Exception as e:
            _save_failed(e, food["name"])
            return

        refresh()  # the new food must show up in the grid picker
        nutrient_count = len(values) + len(food_attributes)
        nutrient_count += int("amino_acids_mg_per_100g" in food)
        st.success(f"Added {food['name']} with {nutrient_count} nutrient values")
