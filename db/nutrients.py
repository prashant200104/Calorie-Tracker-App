"""Single source of truth for nutrient columns.

Every nutrient in `foods` is stored per 100 g. This registry maps a short key
(used in DataFrames and the UI) to its column, label, unit and group, so
analytics and both forms stay in sync when a column is added.

NULL in the DB means "not known"; 0 means "measured as zero".
"""

# key, column, label, unit, group
NUTRIENTS = [
    # ---------------- Macros ----------------
    ("calories",     "calories_per_100g",         "Calories",        "kcal", "Macros"),
    ("protein",      "protein_per_100g",          "Protein",         "g",    "Macros"),
    ("carbs",        "carbohydrates_per_100g",    "Carbs",           "g",    "Macros"),
    ("sugar",        "sugar_per_100g",            "Total sugar",     "g",    "Macros"),
    ("added_sugar",  "added_sugar_g_per_100g",    "Added sugar",     "g",    "Macros"),
    ("fiber",        "fiber_per_100g",            "Fiber",           "g",    "Macros"),
    ("fat",          "fat_per_100g",              "Fat",             "g",    "Macros"),

    # ---------------- Fat types ----------------
    ("mufa",         "mufa_g_per_100g",          "MUFA",            "g",    "Good fats"),
    ("pufa",         "pufa_g_per_100g",          "PUFA",            "g",    "Good fats"),
    ("omega3_ala",   "omega3_ala_g_per_100g",    "Omega-3 (ALA)",   "g",    "Good fats"),
    ("omega3_epa",   "omega3_epa_mg_per_100g",   "Omega-3 (EPA)",   "mg",   "Good fats"),
    ("omega3_dha",   "omega3_dha_mg_per_100g",   "Omega-3 (DHA)",   "mg",   "Good fats"),
    ("omega6_la",    "omega6_la_g_per_100g",     "Omega-6 (LA)",    "g",    "Good fats"),
    ("bad_fat",      "bad_fat_per_100g",         "Saturated fat",   "g",    "Bad fats"),
    ("trans_fat",    "trans_fat_g_per_100g",     "Trans fat",       "g",    "Bad fats"),
    ("cholesterol",  "cholesterol_mg_per_100g",  "Cholesterol",     "mg",   "Other"),

    # ---------------- Minerals ----------------
    ("sodium",       "sodium_mg_per_100g",        "Sodium",          "mg",   "Minerals"),
    ("calcium",      "calcium_mg_per_100g",       "Calcium",         "mg",   "Minerals"),
    ("iron",         "iron_mg_per_100g",          "Iron",            "mg",   "Minerals"),
    ("magnesium",    "magnesium_mg_per_100g",     "Magnesium",       "mg",   "Minerals"),
    ("phosphorus",   "phosphorus_mg_per_100g",    "Phosphorus",      "mg",   "Minerals"),
    ("potassium",    "potassium_mg_per_100g",     "Potassium",       "mg",   "Minerals"),
    ("zinc",         "zinc_mg_per_100g",          "Zinc",            "mg",   "Minerals"),
    ("copper",       "copper_mg_per_100g",        "Copper",          "mg",   "Minerals"),
    ("manganese",    "manganese_mg_per_100g",     "Manganese",       "mg",   "Minerals"),
    ("selenium",     "selenium_mcg_per_100g",     "Selenium",        "mcg",  "Minerals"),
    ("iodine",       "iodine_mcg_per_100g",       "Iodine",          "mcg",  "Minerals"),
    ("chromium",     "chromium_mcg_per_100g",     "Chromium",        "mcg",  "Minerals"),

    # ---------------- Vitamins ----------------
    ("vitamin_a",    "vitamin_a_mcg_per_100g",    "Vitamin A (RAE)", "mcg",  "Vitamins"),
    ("vitamin_c",    "vitamin_c_mg_per_100g",     "Vitamin C",       "mg",   "Vitamins"),
    ("vitamin_d",    "vitamin_d_mcg_per_100g",    "Vitamin D",       "mcg",  "Vitamins"),
    ("vitamin_e",    "vitamin_e_mg_per_100g",     "Vitamin E",       "mg",   "Vitamins"),
    ("vitamin_k",    "vitamin_k_mcg_per_100g",    "Vitamin K",       "mcg",  "Vitamins"),
    ("vitamin_k2",   "vitamin_k2_mcg_per_100g", "Vitamin K2",      "mcg",  "Vitamins"),
    ("thiamine",     "thiamine_mg_per_100g",      "Thiamine (B1)",   "mg",   "Vitamins"),
    ("riboflavin",   "riboflavin_mg_per_100g",    "Riboflavin (B2)", "mg",   "Vitamins"),
    ("niacin",       "niacin_mg_per_100g",        "Niacin (B3)",     "mg",   "Vitamins"),
    ("vitamin_b5",   "vitamin_b5_mg_per_100g",    "Vitamin B5",      "mg",   "Vitamins"),
    ("vitamin_b6",   "vitamin_b6_mg_per_100g",    "Vitamin B6",      "mg",   "Vitamins"),
    ("biotin",       "biotin_mcg_per_100g",       "Biotin",          "mcg",  "Vitamins"),
    ("folate",       "folate_mcg_per_100g",       "Folate",          "mcg",  "Vitamins"),
    ("vitamin_b12",  "vitamin_b12_mcg_per_100g",  "Vitamin B12",     "mcg",  "Vitamins"),

    # ---------------- Amino acids ----------------
    ("leucine",      "leucine_mg_per_100g",      "Leucine",         "mg",   "Amino acids"),
    ("isoleucine",   "isoleucine_mg_per_100g",   "Isoleucine",      "mg",   "Amino acids"),
    ("valine",       "valine_mg_per_100g",       "Valine",          "mg",   "Amino acids"),
    ("lysine",       "lysine_mg_per_100g",       "Lysine",          "mg",   "Amino acids"),
    ("tryptophan",   "tryptophan_mg_per_100g",   "Tryptophan",      "mg",   "Amino acids"),
    ("methionine",   "methionine_mg_per_100g",   "Methionine",      "mg",   "Amino acids"),

    # ---------------- Other ----------------
    ("choline",            "choline_mg_per_100g",            "Choline",            "mg",  "Other"),
    ("lutein_zeaxanthin",  "lutein_zeaxanthin_mcg_per_100g", "Lutein+zeaxanthin",  "mcg", "Other"),
    ("caffeine",           "caffeine_mg_per_100g",          "Caffeine",           "mg",  "Other"),
]

FOOD_ATTRIBUTES = {"glycemic_index": ("Glycemic index", "GI")}

KEYS = [n[0] for n in NUTRIENTS]
COLUMN = {n[0]: n[1] for n in NUTRIENTS}
LABEL = {n[0]: n[2] for n in NUTRIENTS}
UNIT = {n[0]: n[3] for n in NUTRIENTS}
GROUP = {n[0]: n[4] for n in NUTRIENTS}

GROUPS = []
for _n in NUTRIENTS:
    if _n[4] not in GROUPS:
        GROUPS.append(_n[4])

KEYS_IN_GROUP = {g: [n[0] for n in NUTRIENTS if n[4] == g] for g in GROUPS}

# What the dashboard shows before you pick anything else.
DEFAULT_KEYS = ["calories", "protein", "carbs", "fat", "fiber", "sugar", "bad_fat"]

# Columns that are not nutrients, so forms/queries can treat them separately.
META_COLUMNS = ["name", "unit_name", "grams_per_unit", "source", "notes"]


def label_with_unit(key):
    return f"{LABEL[key]} ({UNIT[key]})"
