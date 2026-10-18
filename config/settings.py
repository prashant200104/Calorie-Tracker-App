import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Local dev reads .env above. On Streamlit Cloud there is no .env, so fall back
# to the secrets already configured in the app settings.
if not (SUPABASE_URL and SUPABASE_KEY):
    try:
        import streamlit as st

        SUPABASE_URL = SUPABASE_URL or st.secrets["SUPABASE_URL"]
        SUPABASE_KEY = SUPABASE_KEY or st.secrets["SUPABASE_KEY"]
    except Exception:
        pass

if not (SUPABASE_URL and SUPABASE_KEY):
    raise RuntimeError(
        "SUPABASE_URL / SUPABASE_KEY missing. "
        "Set them in .env for local runs, or in Streamlit secrets when deployed."
    )
