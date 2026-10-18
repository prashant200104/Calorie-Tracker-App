from db.queries import (
    delete_log,
    delete_logs_for_recipe,
    get_log,
    get_logs_for_date,
    insert_log,
    update_log,
)


def add_log(date, food, quantity=None, grams=None, recipe_id=None,
            accumulate=True):
    """Log a food by `quantity` of its named unit, or by raw `grams`.

    `recipe_id` tags the row as part of a meal; None means a standalone entry.

    With `accumulate` (the default), a repeat (date, food, recipe) adds to the
    existing row. With accumulate=False it REPLACES it -- for a per-cook
    ingredient like the oil in a pan, which does not double because you
    cooked more eggs in it.
    """
    grams_value = calculate_grams(food, quantity, grams)
    grams_value = int(round(grams_value))

    if grams_value <= 0:
        raise ValueError("Amount must be greater than 0")

    existing = get_log(date, food["id"], recipe_id)

    if existing:
        new_grams = (
            existing["grams"] + grams_value if accumulate else grams_value
        )
        return update_log(existing["id"], new_grams)

    return insert_log({
        "date": date.isoformat(),
        "food_id": food["id"],
        "grams": grams_value,
        "recipe_id": recipe_id,
    })


def calculate_grams(food, quantity=None, grams=None):
    if grams is not None:
        return grams

    if quantity is not None:
        if food.get("grams_per_unit") is None:
            raise ValueError(
                f"{food['name']} has no grams_per_unit, so it can only be logged by grams"
            )
        return quantity * food["grams_per_unit"]

    raise ValueError("Either quantity or grams must be provided")


def list_logs_for_date(day):
    return get_logs_for_date(day).data or []


def set_log_grams(log_id, grams):
    """Replace an entry's amount outright (unlike add_log, which accumulates)."""
    grams_value = int(round(grams))
    if grams_value <= 0:
        raise ValueError("Amount must be greater than 0")
    return update_log(log_id, grams_value)


def remove_log(log_id):
    return delete_log(log_id)


def remove_meal(day, recipe_id):
    """Delete every entry a meal contributed on that day."""
    return delete_logs_for_recipe(day, recipe_id)
