"""Composite meals, driven entirely by the recipes / recipe_items tables.

Nothing here names a specific food or quantity -- a new meal is a row, and
swapping an ingredient is an UPDATE.
"""

from db.queries import (
    delete_logs_for_recipe,
    get_all_recipes,
    get_recipe_with_items,
    get_recipes_with_items,
)
from services.logs import add_log, remove_log, set_log_grams


def list_recipes():
    return get_all_recipes().data or []


def list_recipes_with_items():
    return get_recipes_with_items().data or []


def get_recipe(recipe_id):
    recipe = get_recipe_with_items(recipe_id)
    if recipe is None:
        raise ValueError(f"Recipe {recipe_id} not found")
    return recipe


def sorted_items(recipe):
    return sorted(recipe.get("recipe_items") or [], key=lambda i: i.get("sort_order", 0))

def item_grams(item, quantity):
    """Grams contributed by one recipe item at `quantity` of its declared unit."""
    food = item["foods"]

    if item["unit"] == "g":
        return float(quantity)

    grams_per_unit = food.get("grams_per_unit")
    if grams_per_unit is None:
        raise ValueError(
            f"{food['name']} is declared in units but has no grams_per_unit; "
            "set one on the food, or change the recipe item to grams"
        )
    return float(quantity) * float(grams_per_unit)


def resolve_quantities(recipe, overrides=None):
    """Pair each item with the quantity to log.

    EVERY ingredient takes the caller's override, falling back to the stored
    quantity: a double batch is two tbsp of oil as well as six eggs, and only
    the person cooking knows that. `is_variable` no longer gates this -- it
    just marks the ingredient the meal is named for, used for the short
    "3 egg" label on the entry row and the tile.
    """
    overrides = overrides or {}
    resolved = []

    for item in sorted_items(recipe):
        quantity = float(overrides.get(item["id"], item["quantity"]))
        if quantity <= 0:
            raise ValueError(
                f"{item['foods']['name']}: quantity must be greater than 0"
            )

        resolved.append((item, quantity, item_grams(item, quantity)))

    return resolved


def log_recipe(date, recipe, overrides=None):
    """Write one daily_logs row per ingredient, each tagged with the recipe."""
    resolved = resolve_quantities(recipe, overrides)

    if not resolved:
        raise ValueError(f"Recipe '{recipe['name']}' has no ingredients")

    for item, _quantity, grams in resolved:
        add_log(
            date=date,
            food=item["foods"],
            grams=grams,
            recipe_id=recipe["id"],
            # Per-cook ingredients replace rather than pile up.
            accumulate=item.get("accumulates", True),
        )

    return resolved

def meal_quantities(recipe, rows):
    """Current quantity of each ingredient, read back from the logs.

    `rows` are that day's daily_logs rows for this recipe. Lets the edit
    dialog open showing "3 eggs" rather than "165 g".
    """
    grams_by_food = {r["food_id"]: float(r["grams"]) for r in rows}
    quantities = {}

    for item in sorted_items(recipe):
        grams = grams_by_food.get(item["food_id"])
        if grams is None:
            quantities[item["id"]] = float(item["quantity"])
        elif item["unit"] == "g":
            quantities[item["id"]] = grams
        else:
            per_unit = item["foods"].get("grams_per_unit") or 1
            quantities[item["id"]] = round(grams / float(per_unit), 2)

    return quantities


def update_meal(day, recipe, rows, overrides):
    """Set a logged meal's amounts outright, rescaling every ingredient.

    Unlike log_recipe (which accumulates), this replaces: editing to 3 eggs
    means 3, not +3. Ingredients already logged are updated in place; any the
    recipe gained since are inserted.
    """
    resolved = resolve_quantities(recipe, overrides)
    row_by_food = {r["food_id"]: r for r in rows}

    for item, _quantity, grams in resolved:
        existing = row_by_food.get(item["food_id"])
        if existing:
            set_log_grams(existing["id"], grams)
        else:
            add_log(day, item["foods"], grams=grams, recipe_id=recipe["id"])

    # Ingredients dropped from the recipe should not linger on the day.
    keep = {item["food_id"] for item, _q, _g in resolved}
    for food_id, row in row_by_food.items():
        if food_id not in keep:
            remove_log(row["id"])

    return resolved


def delete_meal(day, recipe_id):
    return delete_logs_for_recipe(day, recipe_id)
