-- Add drinking water as a selectable food for hydration logging.
-- One millilitre is approximated as one gram.
alter table foods drop column if exists water_g_per_100g;

insert into foods (
    name, unit_name, grams_per_unit, calories_per_100g, protein_per_100g,
    carbohydrates_per_100g, fat_per_100g, fiber_per_100g,
    bad_fat_per_100g, sugar_per_100g
) values (
    'water', 'ml', 1, 0, 0, 0, 0, 0, 0, 0
)
on conflict (name) do update set
    unit_name = excluded.unit_name,
    grams_per_unit = excluded.grams_per_unit,
    calories_per_100g = excluded.calories_per_100g,
    protein_per_100g = excluded.protein_per_100g,
    carbohydrates_per_100g = excluded.carbohydrates_per_100g,
    fat_per_100g = excluded.fat_per_100g,
    fiber_per_100g = excluded.fiber_per_100g,
    bad_fat_per_100g = excluded.bad_fat_per_100g,
    sugar_per_100g = excluded.sugar_per_100g;
