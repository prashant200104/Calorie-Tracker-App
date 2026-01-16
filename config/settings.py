import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# # Add this print statement temporarily to debug
# print(f"DEBUG: URL is {SUPABASE_URL}")
# print(f"DEBUG: KEY is {SUPABASE_KEY}")