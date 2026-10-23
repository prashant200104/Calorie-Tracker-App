"""Settings: choose what appears in the quick-log grid, and add foods.

Everything that is not logging lives here, so the logging screen stays a
single thumb-reachable surface.
"""

import streamlit as st

from services import cache
from services.picks import pick_food, pick_recipe, unpick
from ui.add_food import render_add_food
from ui.nutrition_preview import pretty, unit_label
from ui.quick_log import refresh, refresh_button


def render_settings():
    section = st.segmented_control(
        "Settings section",
        ["Quick-log grid", "Add food"],
        default="Quick-log grid",
        label_visibility="collapsed",
        key="settings_section",
    )

    if section == "Add food":
        render_add_food()
    else:
        render_grid_picker()

    st.divider()
    st.caption(
        "Reads are cached for a few minutes. If you changed something in "
        "Supabase directly, pull it in now."
    )
    refresh_button(key="settings_refresh")


def render_grid_picker():
    st.caption(
        "Pick what shows on your logging screen. Order is handled for you — "
        "whatever you log most floats to the top."
    )

    try:
        picks = cache.picks()
        foods = cache.foods()
        recipes = cache.recipes()
    except Exception as e:
        if "quick_picks" in str(e):
            st.info(
                "Run **db/migrations/005_quick_picks.sql** in Supabase first — "
                "it creates the table that stores your picks."
            )
        else:
            st.error(f"Couldn't load your picks: {e}")
        return

    picked_foods = {p["target_id"]: p for p in picks if p["kind"] == "food"}
    picked_recipes = {p["target_id"]: p for p in picks if p["kind"] == "recipe"}

    st.markdown(f"**On my grid** ({len(picks)})")
    if not picks:
        st.caption("Nothing picked yet — choose some below.")
    else:
        for p in picks:
            tag = " · meal" if p["kind"] == "recipe" else ""
            if st.button(
                f"✓  {pretty(p['label'])}{tag}",
                key=f"unpick_{p['pick_id']}",
                use_container_width=True,
                help="Remove from grid",
            ):
                _toggle(lambda: unpick(p["pick_id"]),
                        f"Removed {pretty(p['label'])}")

    st.divider()

    if recipes:
        st.markdown("**Meals**")
        for recipe in recipes:
            if recipe["id"] in picked_recipes:
                continue
            if st.button(
                f"＋  {pretty(recipe['name'])} · meal",
                key=f"pick_recipe_{recipe['id']}",
                use_container_width=True,
            ):
                _toggle(lambda rid=recipe["id"]: pick_recipe(rid),
                        f"Added {pretty(recipe['name'])}")

    st.markdown("**Foods**")
    search = st.text_input(
        "Search foods", placeholder="Type to filter…", label_visibility="collapsed"
    )

    available = [f for f in foods if f["id"] not in picked_foods]
    if search.strip():
        needle = search.strip().lower().replace(" ", "_")
        available = [f for f in available if needle in f["name"].lower()]

    if not available:
        st.caption("Nothing left to add." if not search.strip() else "No match.")
        return

    for food in available[:40]:
        unit = (
            f" · 1 {unit_label(food.get('unit_name'))} = {food['grams_per_unit']:g} g"
            if food.get("grams_per_unit") else ""
        )
        if st.button(
            f"＋  {pretty(food['name'])}{unit}",
            key=f"pick_food_{food['id']}",
            use_container_width=True,
        ):
            _toggle(lambda fid=food["id"]: pick_food(fid),
                    f"Added {pretty(food['name'])}")

    if len(available) > 40:
        st.caption(f"{len(available) - 40} more — use search to narrow it down.")


def _toggle(action, message):
    try:
        action()
    except Exception as e:
        st.error(str(e))
        return
    refresh()
    st.toast(message, icon="✅")
    st.rerun()
