from db.queries import get_all_foods, insert_food, upsert_food


def list_foods():
    return get_all_foods().data


def add_food(food_dict):
    return insert_food(food_dict)

def save_food(food_dict):
    """Insert, or update in place when that name already exists.

    Imports are re-run (a better source, a corrected label), so a name
    collision means "update this food", not "fail".
    """
    return upsert_food(food_dict)
