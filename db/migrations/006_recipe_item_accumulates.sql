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
