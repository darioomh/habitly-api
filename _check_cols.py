from app.database import supabase

r = supabase.table("challenges").select("*").limit(1).execute()
if r.data:
    print("Columns:", list(r.data[0].keys()))
else:
    print("No challenges")
    # Try to get column info from an insert attempt
    print("Checking table info...")
