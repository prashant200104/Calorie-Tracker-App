from db.connection import supabase

def insert_food(food: dict):
    return supabase.table("foods").insert(food).execute()

def get_all_foods():
    return supabase.table("foods").select("*").order("name").execute()

def insert_log(log: dict):
    return supabase.table("daily_logs").insert(log).execute()

def get_logs_with_foods():
    return supabase.table("daily_logs") \
        .select("date, grams, foods(*)") \
        .execute()


def get_log(date, food_id):
    """Return log row for given date + food_id"""
    response = supabase.table("daily_logs") \
        .select("*") \
        .eq("date", date.isoformat()) \
        .eq("food_id", food_id) \
        .execute()
    if response.data:
        return response.data[0]
    return None

def update_log(log_id, grams):
    return supabase.table("daily_logs") \
        .update({
            "grams": grams,
            "updated_at": "now()"
        }) \
        .eq("id", log_id) \
        .execute()

def insert_log_safe(data):
    return supabase.table("daily_logs").insert(data).execute()  