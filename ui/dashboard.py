import streamlit as st

from analytics.totals import get_daily_totals_for_date, get_weekly_totals
from analytics.targets import compare_daily_targets
from db.nutrients import GROUPS, KEYS_IN_GROUP
from services.logs import list_logs_for_date
from services.recipes import list_recipes_with_items
from ui.date_bar import render_date_bar
from ui.entries import build_entries, render_entries
from ui.log_food import render_log_food
from ui.quick_log import render_quick_log
from ui.settings import render_settings
from ui.theme import day_hero, inject, nutrient_chips, section

NAV_KEY = "nav_section"
SHOW_FULL_FORM = "show_full_form"


def render_dashboard():
    inject()
    tab = st.session_state.get(NAV_KEY, "Log")
    if tab not in ("Log", "Settings"):
        tab = "Log"

    with st.container(key="ctheader"):
        date_column, nav_column = st.columns([0.95, 1.05], vertical_alignment="center")
        with date_column:
            selected_date = render_date_bar()
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

    render_log_section(selected_date)


def render_log_section(selected_date):
    if st.session_state.get(SHOW_FULL_FORM):
        if st.button("← Back", use_container_width=True):
            st.session_state[SHOW_FULL_FORM] = False
            st.rerun()
        render_log_food(selected_date)
        return

    try:
        daily_df = get_daily_totals_for_date(selected_date)
    except Exception as e:
        st.warning(f"Couldn't load totals: {e}")
        daily_df = None

    if daily_df is not None and not daily_df.empty:
        day_hero(daily_df.iloc[0])

    with st.container(key="ctgrid"):
        render_quick_log(selected_date)

    if st.button("Log something else", use_container_width=True):
        st.session_state[SHOW_FULL_FORM] = True
        st.rerun()

    render_day(selected_date, daily_df)


def render_day(selected_date, daily_df):
    try:
        rows = list_logs_for_date(selected_date)
        recipes_by_id = {r["id"]: r for r in list_recipes_with_items()}
    except Exception as e:
        st.warning(f"Couldn't load entries: {e}")
        return

    entries = build_entries(rows, recipes_by_id)

    with st.expander(f"What I ate ({len(entries)})"):
        render_entries(selected_date, entries)

    render_target_comparison(rows)

    if daily_df is None or daily_df.empty:
        return

    totals = daily_df.iloc[0]

    with st.expander("All nutrients"):
        for group in GROUPS:
            keys = [k for k in KEYS_IN_GROUP[group] if totals.get(k)]
            if keys:
                section(group)
                nutrient_chips(totals, keys)

    with st.expander("Last 7 days"):
        weekly_df = get_weekly_totals(selected_date)
        if weekly_df.empty:
            st.caption("No data in the last 7 days.")
        else:
            st.line_chart(
                weekly_df.set_index("date")[["calories", "protein", "carbs", "fat"]]
            )


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
