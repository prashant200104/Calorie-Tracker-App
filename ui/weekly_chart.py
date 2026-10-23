"""The Last 7 days charts.

Calories and macros do NOT share an axis: 2,200 kcal and 180 g on one scale
flattens every macro line onto the floor, which is why one combined line chart
was unreadable. Calories get bars against the daily goal; protein, carbs and
fat get their own grams chart below.

Series colours are per-mode steps, not one set dimmed for dark -- each trio is
validated for the lightness band, chroma floor, colour-vision separation and
contrast against its own surface.
"""

import altair as alt
import pandas as pd
import streamlit as st

from analytics.targets import load_daily_targets

MACRO_KEYS = ["protein", "carbs", "fat"]
MACRO_LABELS = {"protein": "Protein", "carbs": "Carbs", "fat": "Fat"}

# protein, carbs, fat -- and the calorie accent, matching the day hero.
SERIES = {
    "light": {"protein": "#059669", "carbs": "#2563eb", "fat": "#d97706",
              "calories": "#d97706"},
    "dark": {"protein": "#059669", "carbs": "#3b82f6", "fat": "#d97706",
             "calories": "#f59e0b"},
}
INK = {"light": "#475569", "dark": "#cbd5e1"}
MUTED = {"light": "#94a3b8", "dark": "#64748b"}
GRID = {"light": "#e2e8f0", "dark": "#2a3340"}


def _mode():
    """Follow the browser/app theme; assume light if Streamlit can't say."""
    try:
        return "dark" if st.context.theme.type == "dark" else "light"
    except Exception:
        return "light"


def _goal(key):
    for target in load_daily_targets():
        if target["key"] == key and target["mode"] == "goal":
            return float(target["value"])
    return None


def _axes(chart, mode):
    return chart.configure_view(stroke=None).configure_axis(
        domain=False,
        tickColor=GRID[mode],
        gridColor=GRID[mode],
        gridOpacity=0.7,
        labelColor=MUTED[mode],
        titleColor=MUTED[mode],
        labelFontSize=11,
        titleFontSize=11,
    ).configure_legend(
        labelColor=INK[mode],
        titleColor=MUTED[mode],
        labelFontSize=11,
        orient="top",
        direction="horizontal",
        title=None,
        offset=4,
    ).configure_title(
        color=INK[mode], fontSize=12, anchor="start", dy=-4,
    )


def _day_axis(order):
    """Days as an ordinal band: only logged days appear, evenly spaced.

    Labels are the day of the month alone -- seven "Mon 17"s collide at phone
    width, and the title carries the range while the tooltip carries the date.
    """
    return alt.X(
        "day:O",
        title=None,
        sort=order,
        axis=alt.Axis(labelAngle=0, tickSize=0, labelPadding=6),
    )


def _calorie_chart(df, order, mode, span):
    colors = SERIES[mode]
    goal = _goal("calories")

    # The overlay point needs its own colour; mark_line's does not reach it.
    line = alt.Chart(df).mark_line(
        strokeWidth=2,
        color=colors["calories"],
        point=alt.OverlayMarkDef(
            size=60, color=colors["calories"], fill=colors["calories"]
        ),
    ).encode(
        x=_day_axis(order),
        y=alt.Y("calories:Q", title=None, axis=alt.Axis(tickCount=4)),
        tooltip=[
            alt.Tooltip("date:T", title="Day", format="%a %d %b"),
            alt.Tooltip("calories:Q", title="Calories", format=",.0f"),
        ],
    )
    layers = [line]

    if goal:
        goal_df = pd.DataFrame({"goal": [goal]})
        rule = alt.Chart(goal_df).mark_rule(
            color=MUTED[mode], strokeDash=[4, 4], strokeWidth=1
        ).encode(y="goal:Q")
        # Pinned to the left edge: the chart width is the container's, so
        # anything anchored to the right drifts.
        label = alt.Chart(goal_df).mark_text(
            align="left", baseline="bottom", dx=2, dy=-3,
            color=MUTED[mode], fontSize=10,
        ).encode(
            x=alt.value(0), y="goal:Q", text=alt.value(f"goal {goal:,.0f}")
        )
        layers += [rule, label]

    return _axes(
        alt.layer(*layers).properties(
            height=170, title=f"Calories (kcal) · {span}"
        ),
        mode,
    )


def _macro_chart(df, order, mode, span):
    colors = SERIES[mode]
    long_df = df.melt(
        id_vars=["date", "day"], value_vars=MACRO_KEYS,
        var_name="macro", value_name="grams",
    )
    long_df["macro"] = long_df["macro"].map(MACRO_LABELS)

    macro_order = [MACRO_LABELS[k] for k in MACRO_KEYS]
    scale = alt.Scale(domain=macro_order, range=[colors[k] for k in MACRO_KEYS])
    color = alt.Color("macro:N", scale=scale, legend=alt.Legend(title=None))

    base = alt.Chart(long_df)
    lines = base.mark_line(strokeWidth=2, point=alt.OverlayMarkDef(size=60)).encode(
        x=_day_axis(order),
        y=alt.Y("grams:Q", title=None, axis=alt.Axis(tickCount=4)),
        color=color,
        tooltip=[
            alt.Tooltip("date:T", title="Day", format="%a %d %b"),
            alt.Tooltip("macro:N", title="Macro"),
            alt.Tooltip("grams:Q", title="Grams", format=",.1f"),
        ],
    )

    # Each series named at its own last point, so the legend is never the
    # only thing telling them apart.
    last_day = long_df["date"].max()
    labels = alt.Chart(long_df[long_df["date"] == last_day]).mark_text(
        align="left", baseline="middle", dx=6, fontSize=10, color=INK[mode],
    ).encode(x=_day_axis(order), y="grams:Q", text="macro:N")

    return _axes(
        alt.layer(lines, labels).properties(
            height=170,
            title=f"Protein · carbs · fat (g) · {span}",
            padding={"left": 0, "top": 0, "bottom": 0, "right": 44},
        ).resolve_scale(color="shared"),
        mode,
    )


def render_weekly_charts(weekly_df):
    """weekly_df: one row per logged day, as analytics.totals returns it."""
    df = weekly_df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    df["day"] = df["date"].dt.strftime("%-d")
    order = list(df["day"])
    span = f"{df['date'].iloc[0]:%-d %b} – {df['date'].iloc[-1]:%-d %b}"
    mode = _mode()

    st.altair_chart(_calorie_chart(df, order, mode, span), use_container_width=True)
    st.altair_chart(_macro_chart(df, order, mode, span), use_container_width=True)
