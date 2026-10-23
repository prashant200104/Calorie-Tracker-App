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

## Config

[.streamlit/config.toml](.streamlit/config.toml) sets the accent to the app's emerald and turns
off usage stats. It deliberately does **not** set `base`, `backgroundColor` or `textColor`:
Streamlit follows the phone's light/dark setting on its own, and pinning those would freeze the
app in one mode and fight the `prefers-color-scheme` rules in `ui/theme.py`.
`.gitignore` excludes `.streamlit/secrets.toml` only, so this file ships with the repo.

## Architecture

Layered, one direction of dependency: `ui → services → db/queries → db/connection → Supabase`.
`analytics` reads through `db/queries` and returns pandas DataFrames.

```
app.py                 Streamlit entrypoint; just calls render_dashboard()
config/settings.py     loads .env → SUPABASE_URL / SUPABASE_KEY
db/connection.py       creates the module-level `supabase` client
db/queries.py          all raw Supabase table calls (foods, daily_logs)
db/seed_food.py        COMMON_FOODS list (~22 Indian/fitness staples) + seed()
services/cache.py      every read, memoised per session; cache.clear() after writes
services/food_import.py  the JSON schema handed to an LLM, and the parser for its answer
services/foods.py      list_foods(), add_food()
services/logs.py       add_log() — upserts: if a log exists for (date, food_id), adds grams to it
analytics/totals.py    sums nutrients over rows the caller already fetched
ui/dashboard.py        main screen: two action buttons, date picker, 3 tables + line chart
ui/log_food.py         log a food by grams or by units
ui/add_food.py         add a food: paste JSON from an LLM, or type it by hand
ui/clipboard.py        the copy-to-clipboard button (its own iframe)
ui/weekly_chart.py     last 7 days: calorie bars vs goal + a separate macro grams chart
ui/weekly_report.py    last 7 days as plain text + a JS copy-to-clipboard button
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
Water is a food like any other: stored in grams (1 ml ~ 1 g) and shown in whatever unit its
target declares — `"unit": "L"` divides by 1000, `"unit": "ml"` by 1, no code change either way.
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

- **Reads are cached, writes clear the cache.** Every UI read goes through
  [services/cache.py](services/cache.py); `refresh()` (`ui/quick_log.py`) calls `cache.clear()` and must
  follow *any* write, or the screen shows stale data for up to the TTL.
- **Fragments.** The date bar, quick-log grid, entry list and the "Last 7 days" section are
  `@st.fragment`s, so tapping within one re-runs only that block. A write inside a fragment calls
  `st.rerun(scope="app")`, because the hero and the entry list have to catch up.
- **"Last 7 days" is lazy.** An expander body runs even while collapsed, so that section is behind a
  `st.toggle` instead -- its charts and report only cost a query once opened.
- **Added sugar needs an explicit 0.** `_nutrient_inputs` records only values > 0 ("0 means not
  known"), but 0 is the TRUE value for milk, fruit and nuts. The form now writes an explicit 0
  unless "Added sugar not known" is ticked; [db/migrations/009_fix_added_sugar.sql](db/migrations/009_fix_added_sugar.sql)
  backfills the foods that were left NULL.
- **Importing a food upserts on name**, so re-importing is how you correct a food's numbers —
  there is no separate edit screen.
- **No recipe-creation path.** `create_recipe()` / `add_recipe_item()` were removed as dead code;
  meals exist in the schema and log fine, but a new one is made with SQL until a builder screen exists.
- **A dialog closes with an app-scope `st.rerun()`.** A dialog belongs to the page, so
  `st.rerun(scope="fragment")` clears the state behind it and leaves the modal on screen.
- `calculate_grams()`'s `quantity` path is never used: the UI converts units → grams itself
  in [ui/log_food.py](ui/log_food.py).
- `services/logs.py::add_log` *accumulates* grams for a repeat (date, food) pair rather than
  creating a second row. There is no delete/edit-log UI.
- Grams are cast to `int` before insert, so fractional grams are truncated.
- `from datetime import date, timedelta` sits mid-file in [analytics/totals.py:103](analytics/totals.py#L103).
- `requirements.txt` is a full `pip freeze` (76 pinned lines); direct deps are really just
  streamlit, supabase, pandas, python-dotenv.
