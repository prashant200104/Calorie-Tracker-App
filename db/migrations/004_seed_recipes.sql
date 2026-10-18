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
