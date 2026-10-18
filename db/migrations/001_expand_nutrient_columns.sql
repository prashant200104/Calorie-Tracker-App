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

-- ---------- minerals ----------
alter table foods add column if not exists calcium_mg_per_100g    numeric;
alter table foods add column if not exists iron_mg_per_100g       numeric;
alter table foods add column if not exists magnesium_mg_per_100g  numeric;
alter table foods add column if not exists phosphorus_mg_per_100g numeric;
alter table foods add column if not exists potassium_mg_per_100g  numeric;
alter table foods add column if not exists zinc_mg_per_100g       numeric;
alter table foods add column if not exists copper_mg_per_100g     numeric;
alter table foods add column if not exists manganese_mg_per_100g  numeric;
alter table foods add column if not exists selenium_mcg_per_100g  numeric;
alter table foods add column if not exists iodine_mcg_per_100g    numeric;

-- ---------- vitamins ----------
alter table foods add column if not exists vitamin_a_mcg_per_100g   numeric;  -- RAE
alter table foods add column if not exists vitamin_c_mg_per_100g    numeric;
alter table foods add column if not exists vitamin_d_mcg_per_100g   numeric;
alter table foods add column if not exists vitamin_e_mg_per_100g    numeric;
alter table foods add column if not exists vitamin_k_mcg_per_100g   numeric;
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

-- ---------- amino acids ----------
-- Only protein powders declare a full profile, so it lives in one jsonb blob
-- ({"leucine": 5603, ...}, mg per 100 g) rather than 18 sparse columns.
alter table foods add column if not exists amino_acids_mg_per_100g jsonb;

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
