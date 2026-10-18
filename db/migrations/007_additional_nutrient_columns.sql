-- Add nutrients introduced after migration 001. Safe to run against existing foods tables.

-- Fatty-acid details
alter table foods add column if not exists omega3_epa_mg_per_100g numeric;
alter table foods add column if not exists omega3_dha_mg_per_100g numeric;
alter table foods add column if not exists omega6_la_g_per_100g numeric;

-- Minerals and vitamins
alter table foods add column if not exists chromium_mcg_per_100g numeric;
alter table foods add column if not exists vitamin_k2_mcg_per_100g numeric;

-- Individual amino acids
alter table foods add column if not exists leucine_mg_per_100g numeric;
alter table foods add column if not exists isoleucine_mg_per_100g numeric;
alter table foods add column if not exists valine_mg_per_100g numeric;
alter table foods add column if not exists lysine_mg_per_100g numeric;
alter table foods add column if not exists tryptophan_mg_per_100g numeric;
alter table foods add column if not exists methionine_mg_per_100g numeric;

-- Other tracked values
alter table foods add column if not exists glycemic_index numeric;
alter table foods add column if not exists caffeine_mg_per_100g numeric;
