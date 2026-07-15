import os
import sys

# Try to load from .env file manually
try:
    with open(".env", "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key, value)
except FileNotFoundError:
    pass

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")  # Must be the service_role key to bypass RLS

if not SUPABASE_URL or "tu-proyecto" in SUPABASE_URL:
    print("WARNING: Supabase not configured. Using dev mode.")
    supabase = None
else:
    from supabase import create_client, Client
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print(f"Conectado a Supabase!")

def get_db():
    return supabase