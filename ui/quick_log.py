"""One-tap logging for what you actually eat.

Tiles are ranked by recency-weighted frequency and pre-filled with the amount
you used last time. Tapping one opens a small dialog to confirm or change the
amount -- for a meal that means "how many eggs?", for a food its own unit.

Nothing here names a food: the grid is whatever the logs say you eat.
"""

from datetime import date

import streamlit as st

from services import cache
from services.logs import add_log
from services.recipes import item_grams, log_recipe, sorted_items
from ui.nutrition_preview import pretty, show_preview, unit_label, unit_step

COLUMNS = 2
TARGET_KEY = "quick_log_target"


def load_suggestions(day, limit=None):
    return cache.suggestions(day, limit)


def refresh():
    """Call after any write: drops every cached read, not just this grid."""
    cache.clear()


def refresh_button(key="refresh_data"):
    """Pull in changes made outside the app.

    Reads are cached, and a row edited straight in Supabase cannot announce
    itself -- without this the screen quietly disagrees with the database
    until the TTL lapses.
    """
    if st.button("Refresh from database", use_container_width=True, key=key):
        refresh()
        st.toast("Reloaded from the database", icon="🔄")
        st.rerun()


@st.fragment
def render_quick_log(selected_date, limit=None):
    """A fragment: tapping a tile and working the dialog reruns the grid
    alone. Only an actual write reruns the page, to refresh the hero and
    the entry list."""
    try:
        suggestions = load_suggestions(date.today(), limit)
    except Exception as e:
        if "quick_picks" in str(e):
            st.info(
                "Run **db/migrations/005_quick_picks.sql** in Supabase to turn on "
                "the quick-log grid."
            )
        else:
            st.warning(f"Couldn't load your grid: {e}")
        return

    items = suggestions["items"]
    if not items:
        st.info("Your grid is empty. Open **Settings** to pick what shows here.")
        return

    if selected_date != date.today():
        st.caption(f"Logging to **{selected_date:%a %d %b}**.")

    for start in range(0, len(items), COLUMNS):
        cols = st.columns(COLUMNS)
        for col, item in zip(cols, items[start:start + COLUMNS]):
            with col:
                _render_tile(item, selected_date)

    # Opening the dialog is deferred to after the grid is drawn, so the tile
    # that was tapped is still rendered behind the modal. Only the identity is
    # held: looking the item up again each run means an open dialog shows the
    # food as it IS, not as it was when the tile was tapped.
    target = st.session_state.get(TARGET_KEY)
    if target is not None:
        item = next(
            (i for i in items if (i["kind"], i["id"]) == tuple(target)), None
        )
        if item is None:
            _close()
        else:
            _open_dialog(item, selected_date)


def _render_tile(item, selected_date):
    amount = f"{item['default_quantity']:g} {unit_label(item['unit_name'], item['unit_name'])}"
    suffix = " · meal" if item["kind"] == "recipe" else ""
    label = pretty(item["label"])

    if st.button(
        label,
        key=f"quick_{item['kind']}_{item['id']}",
        use_container_width=True,
        help=(
            f"Log {amount}{suffix} — logged {item['times']}× recently"
            if item["times"] else f"Log {amount}{suffix}"
        ),
    ):
        st.session_state[TARGET_KEY] = (item["kind"], item["id"])


def _close():
    st.session_state.pop(TARGET_KEY, None)


# ------------------------------------------------------------------ dialog
def _open_dialog(item, selected_date):
    @st.dialog(f"Log {pretty(item['label'])}")
    def _dialog():
        if item["kind"] == "recipe":
            _recipe_body(item, selected_date)
        else:
            _food_body(item, selected_date)

    _dialog()


def _recipe_body(item, selected_date):
    recipe = item["recipe"]
    previous = item.get("overrides") or {}

    overrides = {}
    parts = []
    invalid = False

    # Every ingredient is askable: cooking two omelettes at once means two
    # tbsp of oil, and nothing but the person at the pan knows that.
    for ri in sorted_items(recipe):
        food = ri["foods"]
        unit = "g" if ri["unit"] == "g" else unit_label(food.get("unit_name"))

        quantity = st.number_input(
            f"{pretty(food['name'])} ({unit})",
            min_value=0.0,
            value=float(previous.get(ri["id"], ri["quantity"])),
            step=1.0 if ri["unit"] == "unit" else 10.0,
            key=f"dlg_item_{ri['id']}",
        )
        overrides[ri["id"]] = quantity

        if quantity <= 0:
            invalid = True
            continue

        try:
            grams = item_grams(ri, quantity)
        except ValueError as e:
            st.error(str(e))
            return

        parts.append((food, grams))

    if parts:
        show_preview(parts, compact=True)

    _actions(
        disabled=invalid or not parts,
        on_log=lambda: log_recipe(
            date=selected_date, recipe=recipe, overrides=overrides
        ),
        label=pretty(recipe["name"]),
    )


def _food_body(item, selected_date):
    food = item["food"]
    grams_per_unit = food.get("grams_per_unit")
    by_grams = item["in_grams"] or not grams_per_unit

    if by_grams:
        grams = st.number_input(
            "Grams",
            min_value=0.0,
            value=float(item["default_quantity"]),
            step=10.0,
            key=f"dlg_grams_{item['id']}",
        )
        quantity = None
        effective = grams
    else:
        unit = unit_label(food.get("unit_name"))
        quantity = st.number_input(
            f"How many {unit}s?",
            min_value=0.0,
            value=float(item["default_quantity"]),
            step=unit_step(grams_per_unit),
            key=f"dlg_units_{item['id']}_{unit}",
        )
        grams = None
        effective = quantity * float(grams_per_unit)
        if effective:
            st.caption(f"= {effective:g} g")

    if effective:
        show_preview([(food, effective)], compact=True)

    _actions(
        disabled=not effective,
        on_log=lambda: add_log(
            date=selected_date, food=food, quantity=quantity, grams=grams
        ),
        label=pretty(food["name"]),
    )


def _actions(disabled, on_log, label):
    col1, col2 = st.columns([2, 1])

    if col1.button("Log it", type="primary", use_container_width=True,
                   disabled=disabled, key="dlg_confirm"):
        try:
            on_log()
        except Exception as e:
            st.error(str(e))
            return
        _close()
        refresh()
        st.toast(f"Logged {label}", icon="✅")
        st.rerun(scope="app")

    if col2.button("Cancel", use_container_width=True, key="dlg_cancel"):
        _close()
        # App scope, not fragment: a dialog belongs to the page, so a
        # fragment-scoped rerun drops the target but leaves the modal open.
        st.rerun()
