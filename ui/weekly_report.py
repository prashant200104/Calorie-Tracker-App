"""Last 7 days as one block of plain text, with a button that copies it.

The text is shaped for a language model to read, not for a person to admire:
a header that states the units and what each column means, then one
pipe-delimited line per item in a fixed field order, ISO dates, and the daily
targets so the model can judge the numbers instead of asking for them. It
stays legible to a human, which is all a paste into a chat needs.

The window always ends today, whatever date the rest of the screen shows.
"""

import json
from datetime import date, timedelta

import streamlit as st
import streamlit.components.v1 as components

from analytics.targets import load_daily_targets
from services import cache
from ui.entries import build_entries
from ui.nutrition_preview import pretty

DAYS = 7

# key, column name in the output, decimals. The order IS the field order of
# every item, total and average line, so it is declared once in the header.
MACROS = [
    ("calories", "kcal", 0),
    ("protein", "protein_g", 1),
    ("carbs", "carbs_g", 1),
    ("fat", "fat_g", 1),
    ("fiber", "fiber_g", 1),
    ("sugar", "sugar_g", 1),
    ("added_sugar", "added_sugar_g", 1),
    ("bad_fat", "satfat_g", 1),
]
FIELDS = [name for _key, name, _digits in MACROS]


def _amount(value, digits):
    formatted = f"{value:,.{digits}f}".replace(",", "")
    if "." in formatted:
        formatted = formatted.rstrip("0").rstrip(".")
    return formatted


def _values(nutrients):
    """The macro columns, in FIELDS order, pipe-delimited."""
    return " | ".join(
        _amount(nutrients.get(key, 0) or 0, digits)
        for key, _name, digits in MACROS
    )


def _grams(entry):
    rows = entry["rows"] if entry["kind"] == "meal" else [entry["row"]]
    return sum(float(r["grams"]) for r in rows)


def _targets_line():
    """What the numbers are supposed to look like, so a model need not ask."""
    by_key = {t["key"]: t for t in load_daily_targets()}
    parts = []
    for key, name, _digits in MACROS:
        target = by_key.get(key)
        if not target:
            continue
        value = _amount(float(target["value"]), 1)
        if target["mode"] == "goal":
            parts.append(f"{name} {value} (goal)")
        elif target["mode"] == "zero":
            parts.append(f"{name} 0 (avoid)")
        else:
            parts.append(f"{name} <={value} (limit)")
    return " | ".join(parts)


def _window():
    end = date.today()
    return end - timedelta(days=DAYS - 1), end


def build_report():
    """The text itself. Returns None when nothing was logged in the window."""
    start, end = _window()
    rows = cache.logs_between(start, end)
    recipes_by_id = {r["id"]: r for r in cache.recipes_with_items()}

    by_day = {}
    for row in rows:
        by_day.setdefault(str(row["date"]), []).append(row)

    totals = {key: 0.0 for key, _name, _digits in MACROS}
    days_with_food = 0

    lines = [
        f"# Food log — {start.isoformat()} to {end.isoformat()} (last {DAYS} days)",
        "",
        "Energy in kcal, everything else in grams, per portion actually eaten.",
        "sugar_g is TOTAL sugar; added_sugar_g counts only added/free sugar — "
        "the sugar in milk, fruit and plain dairy is NOT added sugar.",
        "satfat_g is saturated fat.",
        f"Item line: name | amount | {' | '.join(FIELDS)}",
        f"Daily targets: {_targets_line()}",
        "",
    ]

    for offset in range(DAYS - 1, -1, -1):
        day = end - timedelta(days=offset)
        entries = build_entries(by_day.get(day.isoformat(), []), recipes_by_id)

        lines.append(f"## {day.isoformat()} ({day:%a})")
        if not entries:
            lines.append("no food logged")
            lines.append("")
            continue

        day_totals = {key: 0.0 for key, _name, _digits in MACROS}
        for entry in entries:
            nutrients = entry["nutrients"]
            for key in day_totals:
                day_totals[key] += nutrients.get(key, 0) or 0

            amount = entry["amount"]
            grams = _grams(entry)
            if not amount.endswith(" g"):
                amount = f"{amount} ({_amount(grams, 0)} g)"
            kind = " [meal]" if entry["kind"] == "meal" else ""
            lines.append(
                f"{pretty(entry['label'])}{kind} | {amount} | {_values(nutrients)}"
            )

        for key in totals:
            totals[key] += day_totals[key]
        days_with_food += 1

        lines.append(f"DAY TOTAL | — | {_values(day_totals)}")
        lines.append("")

    if not days_with_food:
        return None

    average = {key: value / days_with_food for key, value in totals.items()}
    lines += [
        "## summary",
        f"days with food logged: {days_with_food} of {DAYS}",
        f"DAILY AVERAGE | — | {_values(average)}",
    ]

    return "\n".join(lines)


def _copy_button(text):
    """A real clipboard button; Streamlit has no native one.

    navigator.clipboard needs a secure context, so a hidden-textarea
    execCommand fallback keeps it working over plain http on the LAN.
    """
    payload = json.dumps(text)
    components.html(
        f"""
<style>
  :root {{ color-scheme: light dark; }}
  html, body {{ margin: 0; }}
  button {{
    width: 100%;
    padding: .55rem .75rem;
    font: 600 .9rem/1.2 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    color: #fff;
    background: #10b981;
    border: 0;
    border-radius: .5rem;
    cursor: pointer;
  }}
  button:active {{ opacity: .85; }}
  button.done {{ background: #059669; }}
</style>
<button id="ct-copy">Copy last 7 days</button>
<script>
  const text = {payload};
  const button = document.getElementById("ct-copy");

  function fallback() {{
    const area = document.createElement("textarea");
    area.value = text;
    area.style.position = "fixed";
    area.style.opacity = "0";
    document.body.appendChild(area);
    area.select();
    let ok = false;
    try {{ ok = document.execCommand("copy"); }} catch (e) {{ ok = false; }}
    document.body.removeChild(area);
    return ok;
  }}

  function done(ok) {{
    button.textContent = ok ? "Copied ✓" : "Press ⌘/Ctrl+C";
    button.classList.toggle("done", ok);
    if (!ok) fallback();
    setTimeout(() => {{
      button.textContent = "Copy last 7 days";
      button.classList.remove("done");
    }}, 2000);
  }}

  button.addEventListener("click", () => {{
    if (navigator.clipboard && window.isSecureContext) {{
      navigator.clipboard.writeText(text).then(() => done(true), () => done(fallback()));
    }} else {{
      done(fallback());
    }}
  }});
</script>
""",
        height=46,
    )


def render_copy_last_7_days():
    try:
        report = build_report()
    except Exception as e:
        st.caption(f"Couldn't build the 7-day report: {e}")
        return

    if report is None:
        st.caption("Nothing logged in the last 7 days.")
        return

    _copy_button(report)
