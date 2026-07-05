import os
from dotenv import load_dotenv
from supabase import create_client

# This file connects the project to Supabase so other files can read and save data.

# Loads secret values like SUPABASE_URL and SUPABASE_ANON_KEY from the .env file.
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

# Creates one Supabase client that the rest of the project imports and uses.
supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
