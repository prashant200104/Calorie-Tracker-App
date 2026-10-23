from db.connection import supabase

# ----------------------------------------------------------------- foods
def insert_food(food: dict):
    return supabase.table("foods").insert(food).execute()

def upsert_food(food: dict):
    """Insert, or update in place if a food with that name already exists.

    Requires the unique constraint on foods.name added by migration 001.
    """
    return supabase.table("foods").upsert(food, on_conflict="name").execute()

def get_all_foods():
    return supabase.table("foods").select("*").order("name").execute()

def get_food_by_name(name: str):
    response = supabase.table("foods") \
        .select("*") \
        .eq("name", name) \
        .limit(1) \
        .execute()
    return response.data[0] if response.data else None


# --------------------------------------------------------------- recipes
def get_all_recipes(active_only=True):
    query = supabase.table("recipes").select("*")
    if active_only:
        query = query.eq("is_active", True)
    return query.order("name").execute()

def get_recipe_with_items(recipe_id):
    """Return a recipe plus its items, each item carrying its full food row."""
    response = supabase.table("recipes") \
        .select("*, recipe_items(*, foods(*))") \
        .eq("id", recipe_id) \
        .limit(1) \
        .execute()
    return response.data[0] if response.data else None

def get_recipes_with_items(active_only=True):
    query = supabase.table("recipes").select("*, recipe_items(*, foods(*))")
    if active_only:
        query = query.eq("is_active", True)
    return query.order("name").execute()

def upsert_recipe(recipe: dict):
    return supabase.table("recipes").upsert(recipe, on_conflict="name").execute()

def insert_recipe_item(item: dict):
    return supabase.table("recipe_items") \
        .upsert(item, on_conflict="recipe_id,food_id") \
        .execute()

def delete_recipe_item(item_id):
    return supabase.table("recipe_items").delete().eq("id", item_id).execute()

def delete_recipe(recipe_id):
    """recipe_items cascade; daily_logs.recipe_id is set to null."""
    return supabase.table("recipes").delete().eq("id", recipe_id).execute()


# ------------------------------------------------------------ daily logs
def insert_log(log: dict):
    return supabase.table("daily_logs").insert(log).execute()

def get_logs_with_foods():
    return supabase.table("daily_logs") \
        .select("date, grams, recipe_id, foods(*)") \
        .execute()

def get_recent_logs(since_date, limit=2000):
    """Logs since `since_date`, newest first, for ranking quick-log suggestions.

    Date-bounded on purpose: this powers a screen that renders on every
    interaction, so it must not grow with total history.
    """
    return supabase.table("daily_logs") \
        .select("id, date, grams, food_id, recipe_id") \
        .gte("date", since_date.isoformat()) \
        .order("date", desc=True) \
        .limit(limit) \
        .execute()

def get_logs_for_date(day):
    """Full rows for one day, including id and meal name, for edit/delete."""
    return supabase.table("daily_logs") \
        .select("id, date, grams, food_id, recipe_id, foods(*), recipes(name)") \
        .eq("date", day.isoformat()) \
        .execute()

def get_logs_between(start_date, end_date):
    """Full rows for an inclusive date range, filtered DB-side."""
    return supabase.table("daily_logs") \
        .select("id, date, grams, food_id, recipe_id, foods(*), recipes(name)") \
        .gte("date", start_date.isoformat()) \
        .lte("date", end_date.isoformat()) \
        .order("date") \
        .execute()

def delete_log(log_id):
    return supabase.table("daily_logs").delete().eq("id", log_id).execute()

def get_log(date, food_id, recipe_id=None):
    """Return the log row for this (date, food, recipe) triple, or None.

    recipe_id is part of the identity: a tagged row from a meal must not
    absorb a plain entry for the same food on the same day, or the meal
    grouping breaks.
    """
    query = supabase.table("daily_logs") \
        .select("*") \
        .eq("date", date.isoformat()) \
        .eq("food_id", food_id)

    if recipe_id is None:
        query = query.is_("recipe_id", "null")
    else:
        query = query.eq("recipe_id", recipe_id)

    response = query.execute()
    return response.data[0] if response.data else None

def update_log(log_id, grams):
    return supabase.table("daily_logs") \
        .update({"grams": grams, "updated_at": "now()"}) \
        .eq("id", log_id) \
        .execute()

def delete_logs_for_recipe(date, recipe_id):
    """Remove every row a given meal contributed on a date."""
    return supabase.table("daily_logs") \
        .delete() \
        .eq("date", date.isoformat()) \
        .eq("recipe_id", recipe_id) \
        .execute()


# ---------------------------------------------------------- quick picks
def get_quick_picks():
    """The user's chosen grid, with the food or recipe attached."""
    return supabase.table("quick_picks") \
        .select("*, foods(*), recipes(*, recipe_items(*, foods(*)))") \
        .order("sort_order") \
        .execute()

def add_quick_pick(food_id=None, recipe_id=None, sort_order=0):
    return supabase.table("quick_picks").insert({
        "food_id": food_id,
        "recipe_id": recipe_id,
        "sort_order": sort_order,
    }).execute()

def remove_quick_pick(pick_id):
    return supabase.table("quick_picks").delete().eq("id", pick_id).execute()
