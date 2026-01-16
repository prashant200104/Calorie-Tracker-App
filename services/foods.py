from db.queries import get_all_foods, insert_food

def list_foods():
    return get_all_foods().data

def add_food(food_dict):
    return insert_food(food_dict)
