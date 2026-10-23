"""The quick-log grid is whatever the user picked -- nothing is inferred.

A pick is a row in `quick_picks` naming either a food or a recipe. Ordering
within the picks is handled by services.suggestions (by how often you log
them), so there is no sort_order to maintain by hand.
"""

from db.queries import add_quick_pick, get_quick_picks, remove_quick_pick


def list_picks():
    """[{id, kind, target_id, label, food|recipe}] in stored order."""
    rows = get_quick_picks().data or []
    picks = []

    for row in rows:
        if row.get("recipe_id") and row.get("recipes"):
            picks.append({
                "pick_id": row["id"],
                "kind": "recipe",
                "target_id": row["recipe_id"],
                "label": row["recipes"]["name"],
                "recipe": row["recipes"],
            })
        elif row.get("food_id") and row.get("foods"):
            picks.append({
                "pick_id": row["id"],
                "kind": "food",
                "target_id": row["food_id"],
                "label": row["foods"]["name"],
                "food": row["foods"],
            })

    return picks

def pick_food(food_id):
    return add_quick_pick(food_id=food_id)


def pick_recipe(recipe_id):
    return add_quick_pick(recipe_id=recipe_id)


def unpick(pick_id):
    return remove_quick_pick(pick_id)
