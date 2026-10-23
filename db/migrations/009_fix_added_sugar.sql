-- Added sugar was NULL on every food that had never had it typed in, because
-- the Add Food form records only values > 0 ("0 means not known"). Two
-- consequences, both visible on the Sugar targets:
--
--   * table sugar you logged counted as ZERO added sugar -- its own row was NULL
--   * milk, curd, bananas and the rest held the whole row at "data incomplete"
--
-- Intrinsic sugar (lactose in milk, fructose in fruit) is NOT added sugar, so
-- these get an explicit 0 rather than being left unknown.

update foods set added_sugar_g_per_100g = 100 where name = 'sugar';

update foods set added_sugar_g_per_100g = 0 where name in (
    'amul_taaza_milk',   -- 4.7 g lactose, intrinsic
    'amul_slim_n_trim',
    'curd_plain',
    'almonds',
    'walnuts',
    'carrot',
    'oats',
    'dates',             -- 63 g, all intrinsic fruit sugar
    'ghee',
    'water',
    'random'
);

-- ESTIMATE, not a label value: the pav carries added sugar and the sweet
-- chutney some more. Change it if you have the real number.
update foods set added_sugar_g_per_100g = 2.0 where name = 'vada_pav';

-- Nothing should claim more added sugar than it has sugar.
update foods
   set added_sugar_g_per_100g = sugar_per_100g
 where added_sugar_g_per_100g is not null
   and sugar_per_100g is not null
   and added_sugar_g_per_100g > sugar_per_100g;
