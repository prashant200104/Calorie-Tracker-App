"""Turn a block of JSON into a `foods` row, and describe the shape it wants.

Typing fifty nutrient fields by hand is the worst part of adding a food, so
the schema below is handed to a language model as a prompt, and whatever it
answers comes back through `parse()`. Nothing here touches Streamlit or the
database: it is a pure translation with the checks that keep a hallucinated
field or a string "12 g" from reaching the table.
"""

import json

from db.nutrients import COLUMN, FOOD_ATTRIBUTES, LABEL, NUTRIENTS, UNIT

AMINO_COLUMN = "amino_acids_mg_per_100g"
TEXT_COLUMNS = {"name", "unit_name", "source", "notes"}
NUMERIC_META = {"grams_per_unit"}

# Column -> what it must contain, used for both the prompt and validation.
ALLOWED = (
    {column: f"{LABEL[key]} per 100 g, in {UNIT[key]}" for key, column in COLUMN.items()}
    | {column: f"{label} ({unit})" for column, (label, unit) in FOOD_ATTRIBUTES.items()}
    | {
        "name": "snake_case identifier, e.g. amul_taaza_milk",
        "unit_name": 'the serving noun alone -- "slice", "egg", "scoop". No "1", no grams',
        "grams_per_unit": "grams in one of those units",
        "source": "where the numbers came from: pack label, USDA, estimate",
        "notes": "caveats worth keeping",
        AMINO_COLUMN: "object of amino acid -> mg per 100 g (optional)",
    }
)

# Short keys are accepted too, since that is how a model tends to answer.
SHORT_KEYS = {key: column for key, column in COLUMN.items()}


def schema_prompt(food_name=""):
    """The text to paste into Claude or GPT."""
    target = food_name.strip() or "<food name>"
    lines = [
        f"Fill in this nutrition record for: {target}",
        "",
        "Rules:",
        "- Every nutrient value is PER 100 g of the food, as a plain number.",
        "- Use null when you genuinely do not know a value. Do NOT guess.",
        "- Use 0 only when the real value is zero. In particular "
        f"{COLUMN['added_sugar']} is 0 for whole foods: the sugar in milk, "
        "fruit, nuts and plain dairy is not added sugar.",
        f"- {COLUMN['added_sugar']} can never exceed {COLUMN['sugar']}.",
        "- Prefer the pack label; otherwise USDA FoodData Central. Say which "
        "in `source`, and put any caveat in `notes`.",
        "- Reply with JSON only, no commentary. A JSON array adds several foods.",
        "",
        "Fields (fill the values, keep the keys exactly):",
        "{",
    ]

    for key, column, label, unit, group in NUTRIENTS:
        lines.append(f'  "{column}": null,   // {label}, {unit} per 100 g [{group}]')
    for column, (label, unit) in FOOD_ATTRIBUTES.items():
        lines.append(f'  "{column}": null,   // {label} ({unit})')
    lines += [
        f'  "{AMINO_COLUMN}": null,   // optional {{"leucine": 5603, ...}} mg per 100 g',
        '  "unit_name": null,   // "slice" / "egg" / "scoop" -- the noun only',
        '  "grams_per_unit": null,   // grams in one of those',
        '  "source": null,',
        '  "notes": null,',
        f'  "name": "{_clean_name(target) if food_name.strip() else "snake_case_name"}"',
        "}",
    ]
    return "\n".join(lines)


class ImportError_(ValueError):
    """Raised with a message meant to be shown to the person pasting."""


def _number(column, value):
    if isinstance(value, bool):
        raise ImportError_(f"{column}: expected a number, got {value!r}")
    if isinstance(value, (int, float)):
        number = float(value)
    else:
        text = str(value).strip().rstrip("%").replace(",", "")
        for unit in ("kcal", "mcg", "µg", "mg", "ml", "g"):
            if text.lower().endswith(unit):
                text = text[: -len(unit)].strip()
                break
        try:
            number = float(text)
        except ValueError:
            raise ImportError_(f"{column}: expected a number, got {value!r}")
    if number < 0:
        raise ImportError_(f"{column}: cannot be negative ({number})")
    return number


def _clean_name(value):
    return str(value).strip().lower().replace(" ", "_")


def parse_one(raw):
    """One JSON object -> (row, ignored_keys). Raises ImportError_ on bad input."""
    if not isinstance(raw, dict):
        raise ImportError_("Each entry must be a JSON object.")

    row = {}
    ignored = []

    for key, value in raw.items():
        column = key if key in ALLOWED else SHORT_KEYS.get(key)
        if column is None:
            ignored.append(key)
            continue
        if value is None or (isinstance(value, str) and not value.strip()):
            continue  # not known: leave the column NULL

        if column == AMINO_COLUMN:
            if isinstance(value, str):
                try:
                    value = json.loads(value)
                except json.JSONDecodeError:
                    raise ImportError_(f"{column}: not valid JSON")
            if not isinstance(value, dict):
                raise ImportError_(f"{column}: expected an object of amino acid -> mg")
            row[column] = {k: _number(f"{column}.{k}", v) for k, v in value.items()}
        elif column == "name":
            row[column] = _clean_name(value)
        elif column in TEXT_COLUMNS:
            row[column] = str(value).strip()
        elif column in NUMERIC_META or column in ALLOWED:
            row[column] = _number(column, value)

    if not row.get("name"):
        raise ImportError_('Missing "name".')

    sugar = row.get(COLUMN["sugar"])
    added = row.get(COLUMN["added_sugar"])
    if sugar is not None and added is not None and added > sugar:
        raise ImportError_(
            f"{row['name']}: added sugar ({added}) is more than total sugar ({sugar})."
        )

    if row.get("unit_name") and not row.get("grams_per_unit"):
        raise ImportError_(
            f"{row['name']}: unit_name \"{row['unit_name']}\" needs grams_per_unit."
        )

    return row, ignored


def parse(text):
    """A pasted blob -> ([row, ...], [ignored key, ...]).

    Accepts one object or an array, and tolerates the ```json fence a chat
    model tends to wrap its answer in.
    """
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.split("\n", 1)[-1]
        if stripped.rstrip().endswith("```"):
            stripped = stripped.rstrip()[:-3]

    if not stripped.strip():
        raise ImportError_("Nothing to import.")

    try:
        data = json.loads(stripped)
    except json.JSONDecodeError as e:
        raise ImportError_(f"Not valid JSON: {e.msg} (line {e.lineno}, column {e.colno})")

    entries = data if isinstance(data, list) else [data]
    rows, ignored = [], []
    for entry in entries:
        row, skipped = parse_one(entry)
        rows.append(row)
        ignored.extend(skipped)

    names = [r["name"] for r in rows]
    duplicates = {n for n in names if names.count(n) > 1}
    if duplicates:
        raise ImportError_(f"The same name appears twice: {', '.join(sorted(duplicates))}")

    return rows, sorted(set(ignored))
