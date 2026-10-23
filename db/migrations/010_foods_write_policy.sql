-- "new row violates row-level security policy for table foods" (42501).
--
-- foods has RLS on with a read policy only, so the app's publishable key can
-- LIST foods but not add one. Logging worked because daily_logs has write
-- policies, and the quick-log grid worked because 005 switched RLS off for
-- quick_picks altogether.
--
-- An upsert needs INSERT *and* UPDATE: re-importing a food to correct its
-- numbers is an update of the row that foods_name_key (001) collides on.
--
-- These policies are open, like the rest of this single-user app. The key
-- lives server-side in Streamlit and never reaches the browser; if it ever
-- leaks, revoke it in Supabase and these policies become moot.

alter table foods enable row level security;

drop policy if exists "foods are readable" on foods;
create policy "foods are readable"
    on foods for select
    using (true);

drop policy if exists "foods can be added" on foods;
create policy "foods can be added"
    on foods for insert
    with check (true);

drop policy if exists "foods can be corrected" on foods;
create policy "foods can be corrected"
    on foods for update
    using (true)
    with check (true);
