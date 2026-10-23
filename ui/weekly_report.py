"""Last 7 days as one block of plain text, with a button that copies it.

Everything logged in the window, day by day: each item with its macros, the
day's total, and the 7-day total -- shaped to be pasted into a chat or a note
rather than read on screen. The window always ends today, whatever date the
rest of the screen is showing.
"""

import json
from datetime import date, timedelta

import streamlit as st
import streamlit.components.v1 as components

from services.logs import list_logs_between
from services.recipes import list_recipes_with_items
from ui.entries import build_entries
from ui.nutrition_preview import pretty

DAYS = 7

# Short labels, because every item line carries all of them.
MACROS = [
    ("calories", "kcal", 0),
    ("protein", "P", 1),
    ("carbs", "C", 1),
    ("fat", "F", 1),
    ("fiber", "Fib", 1),
    ("sugar", "Sug", 1),
    ("bad_fat", "Sat", 1),
]


def _amount(value, digits):
    formatted = f"{value:,.{digits}f}"
    if "." in formatted:
        formatted = formatted.rstrip("0").rstrip(".")
    return formatted


def _macro_line(nutrients):
    parts = []
    for key, label, digits in MACROS:
        value = nutrients.get(key, 0) or 0
        if key == "calories":
            parts.append(f"{_amount(value, digits)} kcal")
        else:
            parts.append(f"{label} {_amount(value, digits)}g")
    return " · ".join(parts)


def _window():
    end = date.today()
    return end - timedelta(days=DAYS - 1), end


def build_report():
    """The text itself. Returns None when nothing was logged in the window."""
    start, end = _window()
    rows = list_logs_between(start, end)
    recipes_by_id = {r["id"]: r for r in list_recipes_with_items()}

    by_day = {}
    for row in rows:
        by_day.setdefault(str(row["date"]), []).append(row)

    totals = {key: 0.0 for key, _, _ in MACROS}
    days_with_food = 0
    lines = [f"Last 7 days · {start:%d %b} – {end:%d %b %Y}", ""]

    for offset in range(DAYS - 1, -1, -1):
        day = end - timedelta(days=offset)
        entries = build_entries(by_day.get(day.isoformat(), []), recipes_by_id)

        lines.append(f"{day:%a %d %b}")
        if not entries:
            lines.append("  nothing logged")
            lines.append("")
            continue

        day_totals = {key: 0.0 for key, _, _ in MACROS}
        for entry in entries:
            nutrients = entry["nutrients"]
            for key in day_totals:
                day_totals[key] += nutrients.get(key, 0) or 0
            suffix = " (meal)" if entry["kind"] == "meal" else ""
            lines.append(
                f"  {pretty(entry['label'])}{suffix} — {entry['amount']} · "
                f"{_macro_line(nutrients)}"
            )

        for key in totals:
            totals[key] += day_totals[key]
        days_with_food += 1

        lines.append(f"  Day total — {_macro_line(day_totals)}")
        lines.append("")

    if not days_with_food:
        return None

    average = {key: value / days_with_food for key, value in totals.items()}
    lines.append(
        f"Daily average ({days_with_food} day"
        f"{'s' if days_with_food != 1 else ''} with food) — {_macro_line(average)}"
    )

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
