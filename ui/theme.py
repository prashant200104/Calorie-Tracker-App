"""Visual layer: one place for colour, spacing and the HTML fragments.

Streamlit's defaults are plain, so the app injects a stylesheet once per run
and renders the richer pieces (day hero, nutrient chips) as HTML. Colours are
defined as custom properties and redefined for dark mode, so the app follows
whatever theme the phone is in.

Nutrient colours stay distinct in the dashboard summary: protein is emerald,
carbs are blue, good fats are amber, bad fats are red, and fibre is teal.
"""

import streamlit as st

from analytics.targets import load_daily_targets
from db.nutrients import LABEL, UNIT

MACRO_COLORS = {
    "calories": "var(--ct-cal)",
    "protein": "var(--ct-protein)",
    "carbs": "var(--ct-carbs)",
    "good_fat": "var(--ct-good-fat)",
    "bad_fat": "var(--ct-bad-fat)",
    "fiber": "var(--ct-fiber)",
}

# Deterministic avatar colours: same food, same colour, forever.
AVATAR_COLORS = [
    "#10b981", "#3b82f6", "#a855f7", "#f59e0b",
    "#ef4444", "#14b8a6", "#ec4899", "#8b5cf6",
]

CSS = """
<style>
:root {
  --ct-accent:  #10b981;
  --ct-cal:     #f59e0b;
  --ct-protein: #10b981;
  --ct-carbs:   #3b82f6;
  --ct-good-fat:#d97706;
  --ct-bad-fat: #dc2626;
  --ct-fiber:   #0e7490;
  --ct-card:    rgba(255,255,255,0.72);
  --ct-border:  rgba(15,23,42,0.10);
  --ct-muted:   rgba(15,23,42,0.58);
  --ct-shadow:  0 1px 2px rgba(15,23,42,0.06), 0 4px 12px rgba(15,23,42,0.05);
}
@media (prefers-color-scheme: dark) {
  :root {
    --ct-card:   rgba(255,255,255,0.045);
    --ct-border: rgba(255,255,255,0.10);
    --ct-muted:  rgba(255,255,255,0.60);
    --ct-shadow: none;
  }
}

/* tighter gutters: this is used one-handed on a phone */
.block-container { padding-top: 2.2rem !important; padding-bottom: 4rem !important; }
@media (max-width: 640px) {
  .block-container { padding-left: 1rem !important; padding-right: 1rem !important; }
}

/* ---------- buttons: cards, not grey slabs ---------- */
.stButton > button {
  border-radius: 14px;
  border: 1px solid var(--ct-border);
  background: var(--ct-card);
  box-shadow: var(--ct-shadow);
  font-weight: 600;
  padding: 0.6rem 0.9rem;
  transition: transform .12s ease, box-shadow .12s ease, border-color .12s ease;
}
.stButton > button:hover {
  border-color: var(--ct-accent);
  transform: translateY(-1px);
}
.stButton > button:active { transform: translateY(0); }
.stButton > button[kind="primary"] {
  background: var(--ct-accent);
  border-color: var(--ct-accent);
  color: #fff;
}

/* ---------- quick-log tiles ---------- */
[class*="st-key-ctgrid"] .stButton > button {
  min-height: 88px;
  white-space: normal;
  line-height: 1.3;
  text-align: left;
  align-items: flex-start;
  padding: 0.7rem 0.65rem;
  font-size: 0.85rem;
  hyphens: auto;
  overflow-wrap: anywhere;
}
/* the amount line under the name reads as secondary */
[class*="st-key-ctgrid"] .stButton > button p:last-child {
  font-weight: 500;
  opacity: 0.62;
  font-size: 0.78rem;
  margin-top: 0.15rem;
}
@media (max-width: 400px) {
  [class*="st-key-ctgrid"] .stButton > button {
    font-size: 0.8rem;
    padding: 0.6rem 0.5rem;
    min-height: 82px;
  }
}
[class*="st-key-quick_recipe_"] .stButton > button,
[class*="st-key-quick_recipe_"] button {
  border-left: 3px solid var(--ct-accent);
}

/* ---------- entry rows ---------- */
details[data-testid="stExpander"], [data-testid="stExpander"] {
  border: 1px solid var(--ct-border) !important;
  border-radius: 14px !important;
  background: var(--ct-card) !important;
  box-shadow: var(--ct-shadow);
  margin-bottom: 0.5rem;
  overflow: hidden;
}
[data-testid="stExpander"] summary { padding: 0.7rem 0.9rem !important; font-weight: 600; }
[data-testid="stExpander"] summary:hover { color: var(--ct-accent); }

/* ---------- hero ---------- */
.ct-hero {
  border: 1px solid var(--ct-border);
  border-radius: 18px;
  background: var(--ct-card);
  box-shadow: var(--ct-shadow);
  padding: 1rem 1.1rem;
  margin: 0.25rem 0 1rem;
}
.ct-hero-top { display: flex; align-items: baseline; gap: .5rem; }
.ct-kcal { font-size: 2.3rem; font-weight: 750; line-height: 1; letter-spacing: -.02em; }
.ct-kcal-unit { font-size: .85rem; color: var(--ct-muted); font-weight: 600; }
.ct-kcal-meta { color: var(--ct-muted); font-size: .8rem; font-weight: 600; margin-top: .35rem; }
.ct-progress { grid-column: 2 / -1; height: 5px; width: 100%; overflow: hidden;
               border-radius: 999px; background: var(--ct-border); }
.ct-progress-fill { display: block; height: 100%; border-radius: inherit; }
.ct-kcal-progress { margin: .55rem 0 .75rem; }
.ct-chips { display: grid; grid-template-columns: minmax(0, 1fr); gap: .4rem; }
.ct-chip { display: grid; grid-template-columns: 8px minmax(5.5rem, max-content) max-content minmax(0, 1fr);
           align-items: center; gap: .35rem; width: 100%;
           font-size: .8rem; color: var(--ct-muted); font-weight: 600; }
.ct-dot { width: 8px; height: 8px; border-radius: 999px; flex: none; }
.ct-chip b { color: inherit; font-weight: 750; }
.ct-chip-detail { color: var(--ct-muted); font-size: .75rem; text-align: right; }
@media (max-width: 400px) {
  .ct-chip-detail { grid-column: 2 / -1; text-align: left; }
}

/* ---------- nutrient chips inside an entry ---------- */
.ct-nutrients { display: flex; flex-wrap: wrap; gap: .35rem; margin: .1rem 0 .6rem; }
.ct-nchip {
  font-size: .74rem; font-weight: 600; color: var(--ct-muted);
  border: 1px solid var(--ct-border); border-radius: 999px;
  padding: .2rem .55rem; background: var(--ct-card); white-space: nowrap;
}
.ct-nchip b { color: inherit; font-weight: 750; }

.ct-section { font-size: .78rem; font-weight: 700; letter-spacing: .04em;
              text-transform: uppercase; color: var(--ct-muted); margin: .9rem 0 .45rem; }
.ct-empty { color: var(--ct-muted); font-size: .88rem; padding: .6rem 0; }
</style>
"""


def inject():
    st.markdown(CSS, unsafe_allow_html=True)


def avatar_color(name):
    return AVATAR_COLORS[sum(map(ord, name)) % len(AVATAR_COLORS)]


def section(text):
    st.markdown(f'<div class="ct-section">{text}</div>', unsafe_allow_html=True)


def empty(text):
    st.markdown(f'<div class="ct-empty">{text}</div>', unsafe_allow_html=True)


def day_hero(totals):
  """Show consumed amounts and remaining daily targets for key nutrients."""
  kcal = totals.get("calories", 0) or 0
  targets = {target["key"]: target for target in load_daily_targets()}

  def amount(value, digits=0):
    formatted = f"{value:,.{digits}f}"
    if "." in formatted:
      formatted = formatted.rstrip("0").rstrip(".")
    return formatted

  def remaining_detail(value, target, unit, label="goal"):
    difference = target - value
    if difference >= 0:
      return f"{amount(difference, 1)} {unit} left"
    return f"{amount(-difference, 1)} {unit} over {label}"

  def progress_line(value, target, color, class_name="ct-progress"):
    percentage = min(max(value / target * 100, 0), 100) if target > 0 else 0
    return (
      f'<div class="{class_name}"><span class="ct-progress-fill" '
      f'style="width:{percentage:.1f}%;background:{color}"></span></div>'
    )

  energy = {
    "protein": (totals.get("protein", 0) or 0) * 4,
    "carbs": (totals.get("carbs", 0) or 0) * 4,
    "fat": (totals.get("fat", 0) or 0) * 9,
  }
  total_energy = sum(energy.values()) or 1
  calorie_target = targets["calories"]["value"]
  calorie_detail = remaining_detail(kcal, calorie_target, "kcal")
  calorie_detail += f" · {kcal / calorie_target * 100:.0f}% target"

  chips = []
  for key in ("protein", "carbs"):
    value = totals.get(key, 0) or 0
    target = targets[key]
    detail = remaining_detail(value, target["value"], target["unit"])
    share = f" · {energy[key] / total_energy * 100:.0f}% kcal"
    chips.append(
      f'<div class="ct-chip"><i class="ct-dot" style="background:'
      f'{MACRO_COLORS[key]}"></i><span>{LABEL[key]}</span>'
      f'<b>{value:.0f}{UNIT[key]}</b>'
      f'<span class="ct-chip-detail">{detail}{share}</span>'
      f'{progress_line(value, target["value"], MACRO_COLORS[key])}</div>'
    )

  polyunsaturated = totals.get("pufa", 0) or 0
  if not polyunsaturated:
    polyunsaturated = (
      (totals.get("omega3_ala", 0) or 0)
      + (totals.get("omega3_epa", 0) or 0) / 1000
      + (totals.get("omega3_dha", 0) or 0) / 1000
      + (totals.get("omega6_la", 0) or 0)
    )
  good_fat = (totals.get("mufa", 0) or 0) + polyunsaturated
  good_fat_target = targets["mufa"]["value"] + targets["pufa"]["value"]
  good_fat_detail = remaining_detail(good_fat, good_fat_target, "g")
  chips.append(
    f'<div class="ct-chip"><i class="ct-dot" style="background:'
    f'{MACRO_COLORS["good_fat"]}"></i><span>Good fat</span>'
    f'<b>{good_fat:.1f}g</b>'
    f'<span class="ct-chip-detail">{good_fat_detail}</span>'
    f'{progress_line(good_fat, good_fat_target, MACRO_COLORS["good_fat"])}</div>'
  )

  saturated = totals.get("bad_fat", 0) or 0
  trans = totals.get("trans_fat", 0) or 0
  bad_fat = saturated + trans
  bad_fat_target = targets["bad_fat"]["value"]
  bad_fat_detail = remaining_detail(bad_fat, bad_fat_target, "g", "limit")
  if trans > 0:
    bad_fat_detail += f" · {trans:.1f}g trans fat"
  chips.append(
    f'<div class="ct-chip"><i class="ct-dot" style="background:'
    f'{MACRO_COLORS["bad_fat"]}"></i><span>Bad fat</span>'
    f'<b>{bad_fat:.1f}g</b>'
    f'<span class="ct-chip-detail">{bad_fat_detail}</span>'
    f'{progress_line(bad_fat, bad_fat_target, MACRO_COLORS["bad_fat"])}</div>'
  )

  fiber = totals.get("fiber", 0) or 0
  fiber_target = targets["fiber"]
  fiber_detail = remaining_detail(fiber, fiber_target["value"], fiber_target["unit"])
  chips.append(
    f'<div class="ct-chip"><i class="ct-dot" style="background:'
    f'{MACRO_COLORS["fiber"]}"></i><span>{LABEL["fiber"]}</span>'
    f'<b>{fiber:.0f}{UNIT["fiber"]}</b>'
    f'<span class="ct-chip-detail">{fiber_detail}</span>'
    f'{progress_line(fiber, fiber_target["value"], MACRO_COLORS["fiber"])}</div>'
  )

  st.markdown(
    '<div class="ct-hero">'
    f'<div class="ct-hero-top"><div class="ct-kcal">{kcal:,.0f}</div>'
    f'<div class="ct-kcal-unit">kcal</div></div>'
    f'<div class="ct-kcal-meta">{calorie_detail}</div>'
    f'{progress_line(kcal, calorie_target, MACRO_COLORS["calories"], "ct-progress ct-kcal-progress")}'
    f'<div class="ct-chips">{"".join(chips)}</div>'
    '</div>',
    unsafe_allow_html=True,
  )


def nutrient_chips(values, keys):
    """Compact pill list of every nutrient with a non-zero value."""
    chips = [
        f'<span class="ct-nchip">{LABEL[k]} <b>{values[k]:.1f}{UNIT[k]}</b></span>'
        for k in keys if values.get(k)
    ]
    if not chips:
        return
    st.markdown(
        f'<div class="ct-nutrients">{"".join(chips)}</div>',
        unsafe_allow_html=True,
    )
