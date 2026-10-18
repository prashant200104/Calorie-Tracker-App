-- Expand `foods` with full macro + micronutrient columns, named serving units,
-- and provenance fields. Run this in the Supabase SQL editor.
--
-- Conventions:
--   * every nutrient is stored PER 100 g
--   * the 7 original columns keep their legacy names (calories_per_100g,
--     protein_per_100g, carbohydrates_per_100g, fat_per_100g, fiber_per_100g,
--     bad_fat_per_100g = saturated fat, sugar_per_100g)
--   * every NEW column carries its unit in the name (_g_, _mg_, _mcg_)
--   * NULL means "not known", 0 means "measured as zero" -- keep that distinction

-- ---------- serving unit + provenance ----------
alter table foods add column if not exists unit_name text;          -- 'slice', 'egg', 'scoop', 'tbsp'
alter table foods add column if not exists source   text;           -- where the numbers came from
alter table foods add column if not exists notes    text;           -- caveats, label inconsistencies

-- ---------- fats & sterols ----------
alter table foods add column if not exists trans_fat_g_per_100g    numeric;
alter table foods add column if not exists mufa_g_per_100g         numeric;
alter table foods add column if not exists pufa_g_per_100g         numeric;
alter table foods add column if not exists omega3_ala_g_per_100g   numeric;
alter table foods add column if not exists cholesterol_mg_per_100g numeric;

-- ---------- carbs & sodium ----------
alter table foods add column if not exists added_sugar_g_per_100g  numeric;
alter table foods add column if not exists sodium_mg_per_100g      numeric;

alter table foods add column if not exists calcium_mg_per_100g    numeric;
alter table foods add column if not exists iron_mg_per_100g       numeric;
alter table foods add column if not exists magnesium_mg_per_100g  numeric;
alter table foods add column if not exists phosphorus_mg_per_100g numeric;
alter table foods add column if not exists potassium_mg_per_100g  numeric;
alter table foods add column if not exists omega3_epa_mg_per_100g  numeric;
alter table foods add column if not exists omega3_dha_mg_per_100g  numeric;
alter table foods add column if not exists omega6_la_g_per_100g    numeric;
alter table foods add column if not exists copper_mg_per_100g     numeric;
alter table foods add column if not exists manganese_mg_per_100g  numeric;
alter table foods add column if not exists selenium_mcg_per_100g  numeric;
alter table foods add column if not exists iodine_mcg_per_100g    numeric;

-- ---------- vitamins ----------
alter table foods add column if not exists vitamin_a_mcg_per_100g   numeric;  -- RAE
alter table foods add column if not exists vitamin_c_mg_per_100g    numeric;
alter table foods add column if not exists vitamin_d_mcg_per_100g   numeric;
alter table foods add column if not exists vitamin_e_mg_per_100g    numeric;
alter table foods add column if not exists chromium_mcg_per_100g  numeric;
alter table foods add column if not exists thiamine_mg_per_100g     numeric;  -- B1
alter table foods add column if not exists riboflavin_mg_per_100g   numeric;  -- B2
alter table foods add column if not exists niacin_mg_per_100g       numeric;  -- B3
alter table foods add column if not exists vitamin_b5_mg_per_100g   numeric;
alter table foods add column if not exists vitamin_b6_mg_per_100g   numeric;
alter table foods add column if not exists biotin_mcg_per_100g      numeric;
alter table foods add column if not exists folate_mcg_per_100g      numeric;
alter table foods add column if not exists vitamin_b12_mcg_per_100g numeric;

-- ---------- other bioactives ----------
alter table foods add column if not exists choline_mg_per_100g            numeric;
alter table foods add column if not exists lutein_zeaxanthin_mcg_per_100g numeric;

alter table foods add column if not exists vitamin_k2_mcg_per_100g numeric;
alter table foods add column if not exists amino_acids_mg_per_100g jsonb;
alter table foods add column if not exists leucine_mg_per_100g     numeric;
alter table foods add column if not exists isoleucine_mg_per_100g  numeric;
alter table foods add column if not exists valine_mg_per_100g      numeric;
alter table foods add column if not exists lysine_mg_per_100g      numeric;
alter table foods add column if not exists tryptophan_mg_per_100g  numeric;
alter table foods add column if not exists methionine_mg_per_100g  numeric;

-- ---------- other tracked values ----------
alter table foods add column if not exists glycemic_index         numeric;
alter table foods add column if not exists caffeine_mg_per_100g    numeric;

-- ---------- make name upsertable ----------
do $$
begin
  if not exists (
    select 1 from pg_constraint
    where conrelid = 'foods'::regclass and contype = 'u'
      and conkey = array[(select attnum from pg_attribute
                          where attrelid = 'foods'::regclass and attname = 'name')]
  ) then
    alter table foods add constraint foods_name_key unique (name);
  end if;
end $$;

-- Drinking water is logged as a food: 1 ml is approximately 1 g.
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

-- ============================================================
-- 002: the six foods, with full macro + micro panels.
-- Every nutrient column is PER 100 g. Safe to re-run: upserts on name,
-- so chia_seeds and health_factory_whole_wheat_bread (already seeded with
-- rougher numbers) get UPDATED in place, not duplicated.
-- ============================================================

-- noice_high_protein_egg: 1 egg = 55 g
insert into foods (
    name,
    unit_name,
    grams_per_unit,
    calories_per_100g,
    protein_per_100g,
    carbohydrates_per_100g,
    sugar_per_100g,
    added_sugar_g_per_100g,
    fiber_per_100g,
    fat_per_100g,
    bad_fat_per_100g,
    trans_fat_g_per_100g,
    mufa_g_per_100g,
    pufa_g_per_100g,
    cholesterol_mg_per_100g,
    sodium_mg_per_100g,
    iron_mg_per_100g,
    phosphorus_mg_per_100g,
    potassium_mg_per_100g,
    zinc_mg_per_100g,
    selenium_mcg_per_100g,
    vitamin_a_mcg_per_100g,
    vitamin_d_mcg_per_100g,
    riboflavin_mg_per_100g,
    folate_mcg_per_100g,
    vitamin_b12_mcg_per_100g,
    choline_mg_per_100g,
    lutein_zeaxanthin_mcg_per_100g,
    source,
    notes
) values (
    'noice_high_protein_egg',
    'egg',
    55,
    143.64,
    12.73,
    0.73,
    0.37,
    0,
    0,
    9.45,
    3.09,
    0,
    3.64,
    2.0,
    372.73,
    141.82,
    1.82,
    198.18,
    138.18,
    1.27,
    30.91,
    160.0,
    2.0,
    0.45,
    47.27,
    0.91,
    294.55,
    254.55,
    'Protein is the brand''s label claim (7 g/egg). Everything else is scaled from USDA whole-egg composition at ~55 g edible egg.',
    'Only protein is a label value; the rest is estimated. ''High protein'' eggs are mostly just bigger eggs -- protein density per gram is near-identical across brands (medium 58 g egg = 6.4 g, large 68 g = 7.5 g). Feed genuinely shifts omega-3, vitamin D, vitamin E and yolk carotenoids, but not protein.'
)
on conflict (name) do update set
    unit_name = excluded.unit_name,
    grams_per_unit = excluded.grams_per_unit,
    calories_per_100g = excluded.calories_per_100g,
    protein_per_100g = excluded.protein_per_100g,
    carbohydrates_per_100g = excluded.carbohydrates_per_100g,
    sugar_per_100g = excluded.sugar_per_100g,
    added_sugar_g_per_100g = excluded.added_sugar_g_per_100g,
    fiber_per_100g = excluded.fiber_per_100g,
    fat_per_100g = excluded.fat_per_100g,
    bad_fat_per_100g = excluded.bad_fat_per_100g,
    trans_fat_g_per_100g = excluded.trans_fat_g_per_100g,
    mufa_g_per_100g = excluded.mufa_g_per_100g,
    pufa_g_per_100g = excluded.pufa_g_per_100g,
    cholesterol_mg_per_100g = excluded.cholesterol_mg_per_100g,
    sodium_mg_per_100g = excluded.sodium_mg_per_100g,
    iron_mg_per_100g = excluded.iron_mg_per_100g,
    phosphorus_mg_per_100g = excluded.phosphorus_mg_per_100g,
    potassium_mg_per_100g = excluded.potassium_mg_per_100g,
    zinc_mg_per_100g = excluded.zinc_mg_per_100g,
    selenium_mcg_per_100g = excluded.selenium_mcg_per_100g,
    vitamin_a_mcg_per_100g = excluded.vitamin_a_mcg_per_100g,
    vitamin_d_mcg_per_100g = excluded.vitamin_d_mcg_per_100g,
    riboflavin_mg_per_100g = excluded.riboflavin_mg_per_100g,
    folate_mcg_per_100g = excluded.folate_mcg_per_100g,
    vitamin_b12_mcg_per_100g = excluded.vitamin_b12_mcg_per_100g,
    choline_mg_per_100g = excluded.choline_mg_per_100g,
    lutein_zeaxanthin_mcg_per_100g = excluded.lutein_zeaxanthin_mcg_per_100g,
    source = excluded.source,
    notes = excluded.notes;

-- health_factory_whole_wheat_bread: 1 slice = 27 g
insert into foods (
    name,
    unit_name,
    grams_per_unit,
    calories_per_100g,
    protein_per_100g,
    carbohydrates_per_100g,
    sugar_per_100g,
    added_sugar_g_per_100g,
    fiber_per_100g,
    fat_per_100g,
    bad_fat_per_100g,
    trans_fat_g_per_100g,
    cholesterol_mg_per_100g,
    sodium_mg_per_100g,
    iron_mg_per_100g,
    magnesium_mg_per_100g,
    phosphorus_mg_per_100g,
    potassium_mg_per_100g,
    zinc_mg_per_100g,
    manganese_mg_per_100g,
    selenium_mcg_per_100g,
    thiamine_mg_per_100g,
    niacin_mg_per_100g,
    folate_mcg_per_100g,
    source,
    notes
) values (
    'health_factory_whole_wheat_bread',
    'slice',
    27,
    241.49,
    13.47,
    43.91,
    4.13,
    1.94,
    6.31,
    1.33,
    0.14,
    0,
    0,
    347.12,
    3.33,
    81.48,
    203.7,
    259.26,
    1.85,
    2.22,
    29.63,
    0.3,
    3.7,
    37.04,
    'Published label per 100 g (cross-checked against HealthifyMe NutriFacts: 65.18 kcal / 3.62 g protein per slice). Micros are estimated from whole wheat atta.',
    '350 g pack = 13 slices (~27 g each). Fibre is inconsistent across the brand''s own pages: the label says 6.31 g/100 g but the 350 g pack page implies ~4.4 g/100 g, and the FAQ says 2 slices give up to 4 g. Treat a slice as 1.2-2.0 g fibre, not a hard number. Indian breads are not fortified, so assume no added folic acid/iron.'
)
on conflict (name) do update set
    unit_name = excluded.unit_name,
    grams_per_unit = excluded.grams_per_unit,
    calories_per_100g = excluded.calories_per_100g,
    protein_per_100g = excluded.protein_per_100g,
    carbohydrates_per_100g = excluded.carbohydrates_per_100g,
    sugar_per_100g = excluded.sugar_per_100g,
    added_sugar_g_per_100g = excluded.added_sugar_g_per_100g,
    fiber_per_100g = excluded.fiber_per_100g,
    fat_per_100g = excluded.fat_per_100g,
    bad_fat_per_100g = excluded.bad_fat_per_100g,
    trans_fat_g_per_100g = excluded.trans_fat_g_per_100g,
    cholesterol_mg_per_100g = excluded.cholesterol_mg_per_100g,
    sodium_mg_per_100g = excluded.sodium_mg_per_100g,
    iron_mg_per_100g = excluded.iron_mg_per_100g,
    magnesium_mg_per_100g = excluded.magnesium_mg_per_100g,
    phosphorus_mg_per_100g = excluded.phosphorus_mg_per_100g,
    potassium_mg_per_100g = excluded.potassium_mg_per_100g,
    zinc_mg_per_100g = excluded.zinc_mg_per_100g,
    manganese_mg_per_100g = excluded.manganese_mg_per_100g,
    selenium_mcg_per_100g = excluded.selenium_mcg_per_100g,
    thiamine_mg_per_100g = excluded.thiamine_mg_per_100g,
    niacin_mg_per_100g = excluded.niacin_mg_per_100g,
    folate_mcg_per_100g = excluded.folate_mcg_per_100g,
    source = excluded.source,
    notes = excluded.notes;

-- cosmix_no_nonsense_plant_protein: 1 scoop = 38 g
insert into foods (
    name,
    unit_name,
    grams_per_unit,
    calories_per_100g,
    protein_per_100g,
    carbohydrates_per_100g,
    sugar_per_100g,
    added_sugar_g_per_100g,
    fiber_per_100g,
    fat_per_100g,
    bad_fat_per_100g,
    trans_fat_g_per_100g,
    cholesterol_mg_per_100g,
    sodium_mg_per_100g,
    iron_mg_per_100g,
    zinc_mg_per_100g,
    amino_acids_mg_per_100g,
    source,
    notes
) values (
    'cosmix_no_nonsense_plant_protein',
    'scoop',
    38,
    370,
    62,
    27.4,
    9.8,
    0,
    9.6,
    1.6,
    0.8,
    0,
    0,
    480,
    12.6,
    6.1,
    '{"alanine": 2529.0, "arginine": 4729.0, "aspartic_acid": 7550.0, "cystine": 310.5, "glutamic_acid": 11860.5, "glycine": 2189.5, "histidine": 1721.1, "isoleucine": 2847.4, "leucine": 5602.6, "lysine": 4789.5, "methionine": 823.7, "phenylalanine": 3171.1, "proline": 3521.1, "serine": 3071.1, "threonine": 2821.1, "tryptophan": 447.4, "tyrosine": 2171.1, "valine": 2979.0}'::jsonb,
    'Pack label (38 g serve, ~26 servings per 1 kg bag), converted to per 100 g.',
    'Leucine is 2.13 g per 38 g scoop, which sits just UNDER the ~2.5 g commonly cited for a maximal MPS trigger -- pea+rice blends need a slightly bigger scoop than whey. Methionine + cystine together are 431 mg/scoop, the usual weak point of pea-dominant blends; the rice isolate patches it, mostly. The 3.7 g sugar per scoop is naturally occurring (coconut milk powder, cacao), not added. Only iron, zinc and sodium are declared -- no calcium, magnesium or B12, so do not count this as a multivitamin.'
)
on conflict (name) do update set
    unit_name = excluded.unit_name,
    grams_per_unit = excluded.grams_per_unit,
    calories_per_100g = excluded.calories_per_100g,
    protein_per_100g = excluded.protein_per_100g,
    carbohydrates_per_100g = excluded.carbohydrates_per_100g,
    sugar_per_100g = excluded.sugar_per_100g,
    added_sugar_g_per_100g = excluded.added_sugar_g_per_100g,
    fiber_per_100g = excluded.fiber_per_100g,
    fat_per_100g = excluded.fat_per_100g,
    bad_fat_per_100g = excluded.bad_fat_per_100g,
    trans_fat_g_per_100g = excluded.trans_fat_g_per_100g,
    cholesterol_mg_per_100g = excluded.cholesterol_mg_per_100g,
    sodium_mg_per_100g = excluded.sodium_mg_per_100g,
    iron_mg_per_100g = excluded.iron_mg_per_100g,
    zinc_mg_per_100g = excluded.zinc_mg_per_100g,
    amino_acids_mg_per_100g = excluded.amino_acids_mg_per_100g,
    source = excluded.source,
    notes = excluded.notes;

-- halim_aliv_seeds: 1 tbsp = 12 g
insert into foods (
    name,
    unit_name,
    grams_per_unit,
    calories_per_100g,
    protein_per_100g,
    carbohydrates_per_100g,
    fiber_per_100g,
    fat_per_100g,
    calcium_mg_per_100g,
    iron_mg_per_100g,
    magnesium_mg_per_100g,
    phosphorus_mg_per_100g,
    niacin_mg_per_100g,
    vitamin_c_mg_per_100g,
    source,
    notes
) values (
    'halim_aliv_seeds',
    'tbsp',
    12,
    458.33,
    25.0,
    33.33,
    9.58,
    24.17,
    375.0,
    22.92,
    433.33,
    725.0,
    14.17,
    66.67,
    'Per-tablespoon figures from Indian composition tables, scaled to 100 g. Iron taken from the 2025 Journal of Agriculture and Food Research review range, not the older tables.',
    'IRON IS CONTESTED. Older Indian tables and most blogs repeat 100 mg/100 g (= 12 mg/tbsp, more than a day''s iron) which looks like a propagated transcription error. A 2025 review says 28.8 mg/100 g, other reviews 17.2 mg, some lab analyses ~5 mg. Stored value is 22.9 mg/100 g = ~2.75 mg/tbsp; plan around 2-3.5 mg/tbsp. The seeds'' own vitamin C aids non-heme absorption -- pair with lemon or amla. Fibre per tbsp is 0.9-1.4 g. Needs 300-350 ml water per serving.'
)
on conflict (name) do update set
    unit_name = excluded.unit_name,
    grams_per_unit = excluded.grams_per_unit,
    calories_per_100g = excluded.calories_per_100g,
    protein_per_100g = excluded.protein_per_100g,
    carbohydrates_per_100g = excluded.carbohydrates_per_100g,
    fiber_per_100g = excluded.fiber_per_100g,
    fat_per_100g = excluded.fat_per_100g,
    calcium_mg_per_100g = excluded.calcium_mg_per_100g,
    iron_mg_per_100g = excluded.iron_mg_per_100g,
    magnesium_mg_per_100g = excluded.magnesium_mg_per_100g,
    phosphorus_mg_per_100g = excluded.phosphorus_mg_per_100g,
    niacin_mg_per_100g = excluded.niacin_mg_per_100g,
    vitamin_c_mg_per_100g = excluded.vitamin_c_mg_per_100g,
    source = excluded.source,
    notes = excluded.notes;

-- chia_seeds: 1 tbsp = 12 g
insert into foods (
    name,
    unit_name,
    grams_per_unit,
    calories_per_100g,
    protein_per_100g,
    carbohydrates_per_100g,
    sugar_per_100g,
    added_sugar_g_per_100g,
    fiber_per_100g,
    fat_per_100g,
    bad_fat_per_100g,
    trans_fat_g_per_100g,
    mufa_g_per_100g,
    pufa_g_per_100g,
    omega3_ala_g_per_100g,
    cholesterol_mg_per_100g,
    sodium_mg_per_100g,
    calcium_mg_per_100g,
    iron_mg_per_100g,
    magnesium_mg_per_100g,
    phosphorus_mg_per_100g,
    potassium_mg_per_100g,
    zinc_mg_per_100g,
    copper_mg_per_100g,
    manganese_mg_per_100g,
    selenium_mcg_per_100g,
    vitamin_c_mg_per_100g,
    vitamin_e_mg_per_100g,
    thiamine_mg_per_100g,
    riboflavin_mg_per_100g,
    niacin_mg_per_100g,
    folate_mcg_per_100g,
    source,
    notes
) values (
    'chia_seeds',
    'tbsp',
    12,
    486,
    16.5,
    42.1,
    0,
    0,
    34.4,
    30.7,
    3.33,
    0,
    2.31,
    23.67,
    17.83,
    0,
    16,
    631,
    7.72,
    335,
    860,
    407,
    4.58,
    0.924,
    2.72,
    55.2,
    1.6,
    0.5,
    0.62,
    0.17,
    8.83,
    49,
    'USDA FoodData Central.',
    '1 tbsp (12 g) = 2.1 g ALA omega-3 and 4.1 g fibre. Absorbs many times its weight in water -- drink enough alongside.'
)
on conflict (name) do update set
    unit_name = excluded.unit_name,
    grams_per_unit = excluded.grams_per_unit,
    calories_per_100g = excluded.calories_per_100g,
    protein_per_100g = excluded.protein_per_100g,
    carbohydrates_per_100g = excluded.carbohydrates_per_100g,
    sugar_per_100g = excluded.sugar_per_100g,
    added_sugar_g_per_100g = excluded.added_sugar_g_per_100g,
    fiber_per_100g = excluded.fiber_per_100g,
    fat_per_100g = excluded.fat_per_100g,
    bad_fat_per_100g = excluded.bad_fat_per_100g,
    trans_fat_g_per_100g = excluded.trans_fat_g_per_100g,
    mufa_g_per_100g = excluded.mufa_g_per_100g,
    pufa_g_per_100g = excluded.pufa_g_per_100g,
    omega3_ala_g_per_100g = excluded.omega3_ala_g_per_100g,
    cholesterol_mg_per_100g = excluded.cholesterol_mg_per_100g,
    sodium_mg_per_100g = excluded.sodium_mg_per_100g,
    calcium_mg_per_100g = excluded.calcium_mg_per_100g,
    iron_mg_per_100g = excluded.iron_mg_per_100g,
    magnesium_mg_per_100g = excluded.magnesium_mg_per_100g,
    phosphorus_mg_per_100g = excluded.phosphorus_mg_per_100g,
    potassium_mg_per_100g = excluded.potassium_mg_per_100g,
    zinc_mg_per_100g = excluded.zinc_mg_per_100g,
    copper_mg_per_100g = excluded.copper_mg_per_100g,
    manganese_mg_per_100g = excluded.manganese_mg_per_100g,
    selenium_mcg_per_100g = excluded.selenium_mcg_per_100g,
    vitamin_c_mg_per_100g = excluded.vitamin_c_mg_per_100g,
    vitamin_e_mg_per_100g = excluded.vitamin_e_mg_per_100g,
    thiamine_mg_per_100g = excluded.thiamine_mg_per_100g,
    riboflavin_mg_per_100g = excluded.riboflavin_mg_per_100g,
    niacin_mg_per_100g = excluded.niacin_mg_per_100g,
    folate_mcg_per_100g = excluded.folate_mcg_per_100g,
    source = excluded.source,
    notes = excluded.notes;

-- cold_pressed_mustard_oil: 1 tbsp = 14 g
insert into foods (
    name,
    unit_name,
    grams_per_unit,
    calories_per_100g,
    protein_per_100g,
    carbohydrates_per_100g,
    sugar_per_100g,
    added_sugar_g_per_100g,
    fiber_per_100g,
    fat_per_100g,
    bad_fat_per_100g,
    trans_fat_g_per_100g,
    mufa_g_per_100g,
    pufa_g_per_100g,
    omega3_ala_g_per_100g,
    cholesterol_mg_per_100g,
    sodium_mg_per_100g,
    source,
    notes
) values (
    'cold_pressed_mustard_oil',
    'tbsp',
    14,
    884,
    0,
    0,
    0,
    0,
    0,
    100,
    11.58,
    0,
    59.19,
    21.23,
    5.9,
    0,
    0,
    'USDA FoodData Central (Oil, mustard).',
    'Logged automatically as the fixed 1 tbsp (14 g) in the omelette shortcut. 1 tbsp = 124 kcal, 14 g fat.'
)
on conflict (name) do update set
    unit_name = excluded.unit_name,
    grams_per_unit = excluded.grams_per_unit,
    calories_per_100g = excluded.calories_per_100g,
    protein_per_100g = excluded.protein_per_100g,
    carbohydrates_per_100g = excluded.carbohydrates_per_100g,
    sugar_per_100g = excluded.sugar_per_100g,
    added_sugar_g_per_100g = excluded.added_sugar_g_per_100g,
    fiber_per_100g = excluded.fiber_per_100g,
    fat_per_100g = excluded.fat_per_100g,
    bad_fat_per_100g = excluded.bad_fat_per_100g,
    trans_fat_g_per_100g = excluded.trans_fat_g_per_100g,
    mufa_g_per_100g = excluded.mufa_g_per_100g,
    pufa_g_per_100g = excluded.pufa_g_per_100g,
    omega3_ala_g_per_100g = excluded.omega3_ala_g_per_100g,
    cholesterol_mg_per_100g = excluded.cholesterol_mg_per_100g,
    sodium_mg_per_100g = excluded.sodium_mg_per_100g,
    source = excluded.source,
    notes = excluded.notes;

-- ============================================================
-- 003: composite meals as DATA.
--
-- A recipe is a row in `recipes`; its ingredients are rows in `recipe_items`
-- referencing foods.id. Adding a meal is an INSERT, never a code change.
--
-- Logging a recipe writes one expanded daily_logs row per ingredient, each
-- tagged with recipe_id -- so per-food analytics stays exact while the meal
-- remains groupable and deletable as a unit.
--
-- recipe_items.is_variable decides whether the log form prompts for that
-- ingredient's amount (eggs) or applies it silently (the fixed tbsp of oil).
-- ============================================================

-- ---------- recipes ----------
create table if not exists recipes (
    id          bigint generated by default as identity primary key,
    name        text not null unique,
    description text,
    notes       text,
    is_active   boolean not null default true,
    created_at  timestamptz not null default now(),
    updated_at  timestamptz not null default now()
);

-- ---------- recipe_items ----------
-- food_id must match foods.id exactly, and this script cannot assume whether
-- that is bigint or uuid, so the column type is read from the catalog.
do $$
declare
    food_id_type text;
begin
    select format_type(atttypid, atttypmod)
      into food_id_type
      from pg_attribute
     where attrelid = 'foods'::regclass
       and attname  = 'id'
       and attnum   > 0
       and not attisdropped;

    if food_id_type is null then
        raise exception 'foods.id not found -- run 001 first';
    end if;

    execute format($fmt$
        create table if not exists recipe_items (
            id          bigint generated by default as identity primary key,
            recipe_id   bigint not null references recipes(id) on delete cascade,
            food_id     %s     not null references foods(id)   on delete restrict,
            quantity    numeric not null check (quantity > 0),
            unit        text    not null default 'unit' check (unit in ('unit', 'g')),
            is_variable boolean not null default false,
            sort_order  integer not null default 0,
            constraint recipe_items_recipe_food_key unique (recipe_id, food_id)
        )
    $fmt$, food_id_type);
end $$;

create index if not exists recipe_items_recipe_id_idx on recipe_items (recipe_id);

-- ---------- tag daily_logs with the meal it came from ----------
alter table daily_logs
    add column if not exists recipe_id bigint references recipes(id) on delete set null;

create index if not exists daily_logs_recipe_id_idx on daily_logs (recipe_id);

-- ---------- keep the accumulate-on-repeat guarantee ----------
-- add_log() accumulates grams for a repeat (date, food, recipe) triple. This
-- index enforces that at the DB level. `nulls not distinct` (PG 15+) is what
-- makes it apply to untagged rows too, where recipe_id is NULL.
--
-- It FAILS if the table already holds duplicate (date, food_id) rows. Check first:
--
--   select date, food_id, count(*)
--     from daily_logs group by 1, 2 having count(*) > 1;
--
-- If that returns rows, consolidate them before creating the index. Skipping
-- this block is safe -- the application still accumulates correctly on its own.
create unique index if not exists daily_logs_date_food_recipe_key
    on daily_logs (date, food_id, recipe_id) nulls not distinct;

-- ---------- updated_at ----------
create or replace function set_updated_at() returns trigger as $$
begin
    new.updated_at = now();
    return new;
end $$ language plpgsql;

drop trigger if exists recipes_set_updated_at on recipes;
create trigger recipes_set_updated_at
    before update on recipes
    for each row execute function set_updated_at();

-- ============================================================
-- 004: the omelette, as data.
--
-- Ingredients are resolved by foods.name, so this depends on 002 having run.
-- Re-runnable: upserts on recipes.name and (recipe_id, food_id).
--
-- To add another meal, copy this block -- no application change is needed.
-- To swap egg brands, update the recipe_items row's food_id.
-- ============================================================

insert into recipes (name, description, notes)
values (
    'omelette',
    'Eggs cooked in cold-pressed mustard oil',
    'Egg count is asked at log time; the oil is fixed at 1 tbsp per omelette.'
)
on conflict (name) do update set
    description = excluded.description,
    notes       = excluded.notes;

-- variable ingredient: prompted at log time
insert into recipe_items (recipe_id, food_id, quantity, unit, is_variable, sort_order)
select r.id, f.id, 1, 'unit', true, 0
  from recipes r
  join foods   f on f.name = 'noice_high_protein_egg'
 where r.name = 'omelette'
on conflict (recipe_id, food_id) do update set
    quantity    = excluded.quantity,
    unit        = excluded.unit,
    is_variable = excluded.is_variable,
    sort_order  = excluded.sort_order;

-- fixed ingredient: applied silently, 1 tbsp
insert into recipe_items (recipe_id, food_id, quantity, unit, is_variable, sort_order)
select r.id, f.id, 1, 'unit', false, 1
  from recipes r
  join foods   f on f.name = 'cold_pressed_mustard_oil'
 where r.name = 'omelette'
on conflict (recipe_id, food_id) do update set
    quantity    = excluded.quantity,
    unit        = excluded.unit,
    is_variable = excluded.is_variable,
    sort_order  = excluded.sort_order;

-- ---------- verify ----------
-- select r.name as recipe, f.name as ingredient, ri.quantity, ri.unit,
--        ri.is_variable, f.grams_per_unit, f.unit_name
--   from recipe_items ri
--   join recipes r on r.id = ri.recipe_id
--   join foods   f on f.id = ri.food_id
--  order by r.name, ri.sort_order;

-- ============================================================
-- 005: the quick-log grid is a list YOU choose.
--
-- One ordered table holding both foods and meals. The grid shows exactly
-- these rows -- nothing is suggested that you did not pick. Within your
-- picks, ordering is by how often you log them, so you never maintain
-- sort_order by hand (it is kept for an explicit manual order later).
-- ============================================================

do $$
declare
    food_id_type text;
begin
    select format_type(atttypid, atttypmod)
      into food_id_type
      from pg_attribute
     where attrelid = 'foods'::regclass
       and attname  = 'id'
       and attnum   > 0
       and not attisdropped;

    if food_id_type is null then
        raise exception 'foods.id not found';
    end if;

    execute format($fmt$
        create table if not exists quick_picks (
            id         bigint generated by default as identity primary key,
            food_id    %s     references foods(id)   on delete cascade,
            recipe_id  bigint references recipes(id) on delete cascade,
            sort_order integer not null default 0,
            created_at timestamptz not null default now(),
            -- exactly one of the two, never both, never neither
            constraint quick_picks_one_target check (
                (food_id is not null and recipe_id is null) or
                (food_id is null and recipe_id is not null)
            )
        )
    $fmt$, food_id_type);
end $$;

-- a thing can only be picked once
create unique index if not exists quick_picks_food_key
    on quick_picks (food_id) where food_id is not null;
create unique index if not exists quick_picks_recipe_key
    on quick_picks (recipe_id) where recipe_id is not null;

alter table quick_picks disable row level security;

-- ============================================================
-- 006: some ingredients are per-cook, not per-portion.
--
-- Logging an omelette twice in a day means more eggs, but NOT more oil --
-- you oiled the pan once. Conflating that with is_variable would be wrong:
-- a sandwich's 2 fixed slices of bread SHOULD double for a second sandwich.
-- So it is its own flag.
--
--   accumulates = true  (default) -> repeat logs add up      (eggs, bread)
--   accumulates = false           -> repeat logs set, not add (oil, pan spray)
-- ============================================================

alter table recipe_items
    add column if not exists accumulates boolean not null default true;

-- the pan is oiled once per cook, however many eggs go in
update recipe_items ri
   set accumulates = false
  from recipes r, foods f
 where ri.recipe_id = r.id
   and ri.food_id   = f.id
   and r.name = 'omelette'
   and f.name = 'cold_pressed_mustard_oil';

-- ---------- verify ----------
-- select r.name as recipe, f.name as ingredient,
--        ri.quantity, ri.is_variable, ri.accumulates
--   from recipe_items ri
--   join recipes r on r.id = ri.recipe_id
--   join foods   f on f.id = ri.food_id
--  order by r.name, ri.sort_order;
