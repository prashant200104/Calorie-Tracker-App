from db.queries import get_log, insert_log_safe, update_log, insert_log

def add_log(date, food, quantity=None, grams=None):
    grams_value = calculate_grams(food, quantity, grams)

    existing = get_log(date, food["id"])

    if existing:
        new_grams = existing["grams"] + grams_value
        return update_log(existing["id"], new_grams)

    return insert_log({
        "date": date.isoformat(),
        "food_id": food["id"],
        "grams": grams_value
    })

def calculate_grams(food, quantity=None, grams=None):
    if grams is not None:
        return grams

    if quantity is not None:
        if food["grams_per_unit"] is None:
            raise ValueError("This food requires grams input")
        return quantity * food["grams_per_unit"]

    raise ValueError("Either quantity or grams must be provided")