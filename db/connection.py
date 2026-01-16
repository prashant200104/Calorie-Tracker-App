from supabase import create_client
from config.settings import SUPABASE_URL, SUPABASE_KEY
# print(f"DEBUG: Connecting to Supabase with URL: {SUPABASE_URL} and KEY: {SUPABASE_KEY}")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# print("DEBUG: Supabase client created successfully")
