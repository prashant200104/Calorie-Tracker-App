-- Log water in litres, not millilitres.
--
-- Storage does not move: water stays a food measured in grams (1 ml ~ 1 g),
-- so every litre already logged keeps its value -- 2000 g simply reads as
-- "2 litre" instead of "2000 ml". Only the serving unit changes.
--
-- The matching target lives in config/daily_targets.json, now 4 L.

update foods
   set unit_name = 'litre',
       grams_per_unit = 1000
 where name = 'water';
