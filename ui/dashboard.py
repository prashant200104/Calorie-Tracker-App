import streamlit as st

from analytics.totals import get_weekly_totals, totals_for_rows
from analytics.targets import compare_daily_targets
from db.nutrients import GROUPS, KEYS_IN_GROUP
from services import cache
from ui.date_bar import get_active_date, render_date_bar
from ui.entries import build_entries, render_entries
from ui.log_food import render_log_food
from ui.quick_log import render_quick_log
from ui.settings import render_settings
from ui.theme import day_hero, inject, nutrient_chips, section
from ui.weekly_chart import render_charts
from ui.weekly_report import render_copy_button

NAV_KEY = "nav_section"
SHOW_FULL_FORM = "show_full_form"
HISTORY_KEY = "history_window"
WINDOWS = (7, 30)


def render_dashboard():
    inject()
    tab = st.session_state.get(NAV_KEY, "Log")
    if tab not in ("Log", "Settings"):
        tab = "Log"

    with st.container(key="ctheader"):
        date_column, nav_column = st.columns([0.95, 1.05], vertical_alignment="center")
        with date_column:
            render_date_bar()
        with nav_column:
            log_column, settings_column = st.columns(2, gap="small")
            if log_column.button(
                "Log",
                type="primary" if tab == "Log" else "secondary",
                key="nav_log",
                use_container_width=True,
            ):
                st.session_state[NAV_KEY] = "Log"
                st.rerun()
            if settings_column.button(
                "Settings",
                type="primary" if tab == "Settings" else "secondary",
                key="nav_settings",
                use_container_width=True,
            ):
                st.session_state[NAV_KEY] = "Settings"
                st.rerun()

    if tab == "Settings":
        render_settings()
        return

    render_log_section(get_active_date())


def render_log_section(selected_date):
    if st.session_state.get(SHOW_FULL_FORM):
        if st.button("← Back", use_container_width=True):
            st.session_state[SHOW_FULL_FORM] = False
            st.rerun()
        render_log_food(selected_date)
        return

    # One fetch for the whole screen: the hero, the entry list and the target
    # table are three views of the same day's rows.
    try:
        rows = cache.logs_for_date(selected_date)
    except Exception as e:
        st.warning(f"Couldn't load the day: {e}")
        rows = []

    totals = totals_for_rows(rows)
    if totals:
        day_hero(totals)

    with st.container(key="ctgrid"):
        render_quick_log(selected_date)

    if st.button("Log something else", use_container_width=True):
        st.session_state[SHOW_FULL_FORM] = True
        st.rerun()

    render_day(selected_date, rows, totals)


def render_day(selected_date, rows, totals):
    try:
        recipes_by_id = {r["id"]: r for r in cache.recipes_with_items()}
    except Exception as e:
        st.warning(f"Couldn't load meals: {e}")
        return

    render_entry_list(selected_date, rows, recipes_by_id)
    render_target_comparison(rows)

    if totals:
        with st.expander("All nutrients"):
            for group in GROUPS:
                keys = [k for k in KEYS_IN_GROUP[group] if totals.get(k)]
                if keys:
                    section(group)
                    nutrient_chips(totals, keys)

    render_history_section(selected_date)


@st.fragment
def render_entry_list(selected_date, rows, recipes_by_id):
    """Its own fragment: opening an entry or editing it reruns this list
    alone, not the whole page."""
    entries = build_entries(rows, recipes_by_id)
    with st.expander(f"What I ate ({len(entries)})"):
        render_entries(selected_date, entries)


@st.fragment
def render_history_section(selected_date):
    """Charts and the copy text are the most expensive things on the screen,
    so nothing is built until a window is picked -- an expander body runs even
    while it is collapsed, which is why this is buttons and not an expander.

    Tapping the open window closes it, so the screen can be quiet again.
    """
    open_days = st.session_state.get(HISTORY_KEY)
    columns = st.columns(len(WINDOWS), gap="small")

    for column, days in zip(columns, WINDOWS):
        if column.button(
            f"Last {days} days",
            type="primary" if open_days == days else "secondary",
            use_container_width=True,
            key=f"history_{days}",
        ):
            st.session_state[HISTORY_KEY] = None if open_days == days else days
            # App scope on purpose: the buttons above have already drawn with
            # the old selection, so something must redraw them, and a
            # fragment-scoped rerun is only legal during a fragment rerun.
            # Every read is cached, so this costs no queries.
            st.rerun()

    if not open_days:
        return

    try:
        daily_df = get_weekly_totals(selected_date, days=open_days)
    except Exception as e:
        st.warning(f"Couldn't load the last {open_days} days: {e}")
        return

    if daily_df.empty:
        st.caption(f"No data in the last {open_days} days.")
    else:
        render_charts(daily_df)

    render_copy_button(open_days)


def _format_target_amount(value):
    return f"{value:,.2f}".rstrip("0").rstrip(".")


def _target_label(target):
    amount = _format_target_amount(target["value"])
    if target["mode"] == "goal":
        return f"{amount} {target['unit']} goal"
    if target["mode"] == "zero":
        return f"0 {target['unit']} target"
    if target["mode"] == "average_limit":
        return f"Average < {amount} {target['unit']}"
    return f"Under {amount} {target['unit']}"


def _target_percentage(result):
    intake = result["intake"]
    target_value = result["value"]
    if intake is None:
        return "No data"
    if target_value == 0:
        return "0%" if intake == 0 else "N/A"

    percentage = intake / target_value * 100
    marker = "*" if result["coverage"] < 1.0 else ""
    return f"{percentage:.0f}%{marker}"


def render_target_comparison(log_rows):
    results = compare_daily_targets(log_rows)
    goals = [result for result in results if result["mode"] == "goal"]
    limits = [result for result in results if result["mode"] != "goal"]
    goals_met = sum(result["status"] == "Covered" for result in goals)
    limits_met = sum(
        result["status"] in ("Within limit", "Target met") for result in limits
    )
    incomplete = sum(result["coverage"] < 1.0 for result in results)

    if not log_rows:
        st.caption("Daily targets: log food to compare your intake.")
    else:
        st.caption(
            f"Daily targets: {goals_met}/{len(goals)} goals covered · "
            f"{limits_met}/{len(limits)} limits met · "
            f"{incomplete} nutrients with incomplete food data"
        )

    with st.expander("Macro / Micro Daily Targets"):
        st.caption(
            "% RDA is progress toward a goal or the share of a maximum limit. "
            "* means the logged foods have incomplete nutrient data."
        )
        rows = []
        for result in results:
            intake = result["intake"]
            rows.append({
                "Group": result["group"],
                "Nutrient": result["label"],
                "Today": (
                    f"{_format_target_amount(intake)} {result['unit']}"
                    if intake is not None else "No data"
                ),
                "Target": _target_label(result),
                "% RDA": _target_percentage(result),
            })
        st.dataframe(rows, hide_index=True, use_container_width=True)
