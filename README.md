# Calorie Tracker App

Streamlit app for logging food intake and tracking macros, backed by Supabase (Postgres).

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

### Credentials

[config/settings.py](config/settings.py) resolves them from two sources, in order:

1. **Local** — a `.env` file (gitignored) in the project root:
   ```
   SUPABASE_URL=https://<project-ref>.supabase.co
   SUPABASE_KEY=sb_publishable_...
   ```
2. **Deployed** — if `.env` is absent (Streamlit Cloud), it falls back to `st.secrets`,
   which is already configured in the app settings. No `secrets.toml` is needed locally.

If neither supplies both values, it raises a `RuntimeError` with a clear message instead
of failing later inside the Supabase client.

Seed the food table once: `python -m db.seed_food`

## Architecture

Layered, one direction of dependency: `ui → services → db/queries → db/connection → Supabase`.
`analytics` reads through `db/queries` and returns pandas DataFrames.

```
app.py                 Streamlit entrypoint; just calls render_dashboard()
config/settings.py     loads .env → SUPABASE_URL / SUPABASE_KEY
db/connection.py       creates the module-level `supabase` client
db/queries.py          all raw Supabase table calls (foods, daily_logs)
db/seed_food.py        COMMON_FOODS list (~22 Indian/fitness staples) + seed()
db/backup.py           empty placeholder
services/foods.py      list_foods(), add_food()
services/logs.py       add_log() — upserts: if a log exists for (date, food_id), adds grams to it
analytics/totals.py    pandas aggregation: daily totals, detailed logs, weekly
ui/dashboard.py        main screen: two action buttons, date picker, 3 tables + line chart
ui/log_food.py         log a food by grams or by units
ui/add_food.py         create a new food (per-100g nutrition)
```

## Data model (Supabase)

**`foods`**
`id`, `name` (lowercased, snake_case), optional serving/provenance fields, per-100g nutrient
columns registered in [db/nutrients.py](db/nutrients.py), and the optional
`amino_acids_mg_per_100g` JSON profile. Run the SQL migrations in `db/migrations/` to set up
the schema; `db/supabase_setup.sql` contains the combined setup script.

**`daily_logs`**
`id`, `date`, `food_id` → foods.id, `grams`, `updated_at`

Nutrition is always stored per 100g; everything else is derived as `grams / 100 * value`.
Personal daily goals and upper limits are stored in [config/daily_targets.json](config/daily_targets.json)
and compared with logged food on the dashboard. Nutrient rows show the share of logged food
with known values so missing database data is not mistaken for zero intake. The target table
groups nutrients in the configured order; `% RDA` shows progress toward a goal or the share
of a maximum limit, with `*` marking incomplete food data.

## UI flow

`ui/dashboard.py` uses `st.session_state.dashboard_view` (`None` | `"log_food"` | `"add_food"`)
as a single-level router. When a view is set, the dashboard renders that form and returns early —
the buttons stay visible on top. Page-level sidebar nav in `app.py` is commented out.

## Known quirks / gotchas

- **No DB-side date filtering.** `analytics/totals.py` pulls *every* log via `get_logs_with_foods()`
  then filters in pandas (`get_daily_totals_for_date`, `get_weekly_totals`). Fine now, will not scale.
- **`add_food.py` never collects `grams_per_unit`**, so foods created in the UI can only be logged
  by grams — "Units" mode shows a warning for them. Only seeded foods have units.
- **Dead code:** `insert_log_safe()` in [db/queries.py](db/queries.py) is unused (`add_log` uses `insert_log`),
  `db/backup.py` is empty, `calculate_grams()`'s `quantity` path is never used (the UI converts
  units → grams itself in [ui/log_food.py](ui/log_food.py)).
- `services/logs.py::add_log` *accumulates* grams for a repeat (date, food) pair rather than
  creating a second row. There is no delete/edit-log UI.
- Grams are cast to `int` before insert, so fractional grams are truncated.
- `from datetime import date, timedelta` sits mid-file in [analytics/totals.py:103](analytics/totals.py#L103).
- `requirements.txt` is a full `pip freeze` (76 pinned lines); direct deps are really just
  streamlit, supabase, pandas, python-dotenv.
