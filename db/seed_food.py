from db.queries import insert_food

COMMON_FOODS = [
  {
    "name": "water",
    "unit_name": "litre",
    "grams_per_unit": 1000,
    "calories_per_100g": 0,
    "protein_per_100g": 0,
    "carbohydrates_per_100g": 0,
    "fat_per_100g": 0,
    "fiber_per_100g": 0,
    "bad_fat_per_100g": 0,
    "sugar_per_100g": 0
  },
  {
    "name": "amul_taaza_milk",
    "grams_per_unit": 100,
    "calories_per_100g": 60,
    "protein_per_100g": 3.1,
    "carbohydrates_per_100g": 4.7,
    "fat_per_100g": 3.0,
    "fiber_per_100g": 0,
    "bad_fat_per_100g": 1.9,
    "sugar_per_100g": 4.7
  },
  {
    "name": "whey_muscleblaze_biozyme",
    "grams_per_unit": 36,
    "calories_per_100g": 361,
    "protein_per_100g": 69.4,
    "carbohydrates_per_100g": 11.1,
    "fat_per_100g": 4.2,
    "fiber_per_100g": 0,
    "bad_fat_per_100g": 2.5,
    "sugar_per_100g": 0
  },
  {
    "name": "pintola_high_protein_muesli",
    "grams_per_unit": 50,
    "calories_per_100g": 390,
    "protein_per_100g": 24.0,
    "carbohydrates_per_100g": 56.0,
    "fat_per_100g": 8.0,
    "fiber_per_100g": 10.0,
    "bad_fat_per_100g": 1.7,
    "sugar_per_100g": 17.0
  },
  {
    "name": "health_factory_whole_wheat_bread",
    "grams_per_unit": 27,
    "calories_per_100g": 245,
    "protein_per_100g": 10.5,
    "carbohydrates_per_100g": 46.0,
    "fat_per_100g": 2.1,
    "fiber_per_100g": 5.5,
    "bad_fat_per_100g": 0.4,
    "sugar_per_100g": 3.5
  },
  {
    "name": "besan_ka_cheela_low_ghee",
    "grams_per_unit": 100,
    "calories_per_100g": 240,
    "protein_per_100g": 18.0,
    "carbohydrates_per_100g": 30.0,
    "fat_per_100g": 4.5,
    "fiber_per_100g": 8.0,
    "bad_fat_per_100g": 0.8,
    "sugar_per_100g": 2.0
  },
  {
    "name": "moong_dal_ka_cheela_low_ghee",
    "grams_per_unit": 100,
    "calories_per_100g": 190,
    "protein_per_100g": 14.0,
    "carbohydrates_per_100g": 26.0,
    "fat_per_100g": 3.0,
    "fiber_per_100g": 6.0,
    "bad_fat_per_100g": 0.5,
    "sugar_per_100g": 1.5
  },
  {
    "name": "oats",
    "grams_per_unit": 40,
    "calories_per_100g": 389,
    "protein_per_100g": 13,
    "carbohydrates_per_100g": 66.3,
    "fat_per_100g": 6.9,
    "fiber_per_100g": 10.6,
    "bad_fat_per_100g": 1.2,
    "sugar_per_100g": 1.0
  },
  {
    "name": "low_fat_paneer",
    "grams_per_unit": 200,
    "calories_per_100g": 200,
    "protein_per_100g": 25.0,
    "carbohydrates_per_100g": 3.0,
    "fat_per_100g": 9.0,
    "fiber_per_100g": 0,
    "bad_fat_per_100g": 6.0,
    "sugar_per_100g": 1.0
  },
  {
    "name": "popcorn_air_popped",
    "grams_per_unit": 20,
    "calories_per_100g": 387,
    "protein_per_100g": 13.0,
    "carbohydrates_per_100g": 78.0,
    "fat_per_100g": 5.0,
    "fiber_per_100g": 14.5,
    "bad_fat_per_100g": 0.7,
    "sugar_per_100g": 0.5
  },
  {
    "name": "chia_seeds",
    "grams_per_unit": 12,
    "calories_per_100g": 486,
    "protein_per_100g": 16.5,
    "carbohydrates_per_100g": 42.1,
    "fat_per_100g": 30.7,
    "fiber_per_100g": 34.4,
    "bad_fat_per_100g": 3.3,
    "sugar_per_100g": 0
  },
  {
    "name": "peanuts",
    "grams_per_unit": 28,
    "calories_per_100g": 567,
    "protein_per_100g": 25.8,
    "carbohydrates_per_100g": 16.1,
    "fat_per_100g": 49.2,
    "fiber_per_100g": 8.5,
    "bad_fat_per_100g": 7.0,
    "sugar_per_100g": 4.0
  },
  {
    "name": "almonds",
    "grams_per_unit": 1.2,
    "calories_per_100g": 579,
    "protein_per_100g": 21.2,
    "carbohydrates_per_100g": 21.6,
    "fat_per_100g": 49.9,
    "fiber_per_100g": 12.5,
    "bad_fat_per_100g": 3.7,
    "sugar_per_100g": 4.4
  },
  {
    "name": "walnuts",
    "grams_per_unit": 4,
    "calories_per_100g": 654,
    "protein_per_100g": 15.2,
    "carbohydrates_per_100g": 13.7,
    "fat_per_100g": 65.2,
    "fiber_per_100g": 6.7,
    "bad_fat_per_100g": 6.1,
    "sugar_per_100g": 2.6
  },
  {
    "name": "curd_plain",
    "grams_per_unit": 100,
    "calories_per_100g": 60,
    "protein_per_100g": 3.5,
    "carbohydrates_per_100g": 4.7,
    "fat_per_100g": 3.0,
    "fiber_per_100g": 0,
    "bad_fat_per_100g": 1.8,
    "sugar_per_100g": 4.7
  },
  {
    "name": "apple",
    "grams_per_unit": 150,
    "calories_per_100g": 52,
    "protein_per_100g": 0.3,
    "carbohydrates_per_100g": 14.0,
    "fat_per_100g": 0.2,
    "fiber_per_100g": 2.4,
    "bad_fat_per_100g": 0,
    "sugar_per_100g": 10.0
  },
  {
    "name": "carrot",
    "grams_per_unit": 100,
    "calories_per_100g": 41,
    "protein_per_100g": 0.9,
    "carbohydrates_per_100g": 10.0,
    "fat_per_100g": 0.2,
    "fiber_per_100g": 2.8,
    "bad_fat_per_100g": 0,
    "sugar_per_100g": 5.0
  },
  {
    "name": "shimla_mirch",
    "grams_per_unit": 100,
    "calories_per_100g": 31,
    "protein_per_100g": 1.0,
    "carbohydrates_per_100g": 6.0,
    "fat_per_100g": 0.3,
    "fiber_per_100g": 2.1,
    "bad_fat_per_100g": 0,
    "sugar_per_100g": 4.0
  },
  {
    "name": "vegetables_mixed",
    "grams_per_unit": 100,
    "calories_per_100g": 30,
    "protein_per_100g": 2.0,
    "carbohydrates_per_100g": 6.0,
    "fat_per_100g": 0.2,
    "fiber_per_100g": 2.0,
    "bad_fat_per_100g": 0,
    "sugar_per_100g": 3.0
  },
  {
    "name": "poha_home_cooked",
    "grams_per_unit": 180,
    "calories_per_100g": 180,
    "protein_per_100g": 3.5,
    "carbohydrates_per_100g": 32.0,
    "fat_per_100g": 4.5,
    "fiber_per_100g": 2.2,
    "bad_fat_per_100g": 0.9,
    "sugar_per_100g": 1.2
  },
  {
    "name": "vada_pav",
    "grams_per_unit": 150,
    "calories_per_100g": 280,
    "protein_per_100g": 6.0,
    "carbohydrates_per_100g": 35.0,
    "fat_per_100g": 13.0,
    "fiber_per_100g": 3.0,
    "bad_fat_per_100g": 4.0,
    "sugar_per_100g": 4.0
  },
  {
    "name": "dates",
    "grams_per_unit": 24,
    "calories_per_100g": 282,
    "protein_per_100g": 2.5,
    "carbohydrates_per_100g": 75.0,
    "fat_per_100g": 0.4,
    "fiber_per_100g": 8.0,
    "bad_fat_per_100g": 0,
    "sugar_per_100g": 63.0
  },
  {
    "name": "sugar",
    "grams_per_unit": 5,
    "calories_per_100g": 387,
    "protein_per_100g": 0,
    "carbohydrates_per_100g": 100.0,
    "fat_per_100g": 0,
    "fiber_per_100g": 0,
    "bad_fat_per_100g": 0,
    "sugar_per_100g": 100.0
  }
]

def seed():
    for food in COMMON_FOODS:
        try:
            insert_food(food)
            print(f"Inserted {food['name']}")
        except Exception as e:
            print(f"Skipping {food['name']}: {e}")

if __name__ == "__main__":
    seed()