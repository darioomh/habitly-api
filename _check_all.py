from app.database import supabase

print("=== CHALLENGES table columns ===")
r = supabase.table("challenges").select("*").limit(1).execute()
cols = list(r.data[0].keys()) if r.data else []
print(cols)

print()
print("=== CHALLENGE_PARTICIPANTS columns ===")
pr = supabase.table("challenge_participants").select("*").limit(1).execute()
pcols = list(pr.data[0].keys()) if pr.data else []
print(pcols)

print()
print("=== HABITS table columns ===")
hr = supabase.table("habits").select("*").limit(1).execute()
hcols = list(hr.data[0].keys()) if hr.data else []
print(hcols)

print()
print("=== EXISTING CHALLENGES ===")
allc = supabase.table("challenges").select("*").execute()
for c in (allc.data or []):
    print(f'  {c["id"][:8]} | {c["category"]:12s} | premium={c.get("is_premium_required")} | {c["title"]}')

print()
print("=== EXISTING HABITS ===")
allh = supabase.table("habits").select("*").execute()
for h in (allh.data or []):
    print(f'  {h["id"][:8]} | {h["category"]:12s} | {h["title"]}')

print()
print("=== CHALLENGE_HABITS ===")
lh = supabase.table("challenge_habits").select("*").execute()
print(f'Links: {len(lh.data or [])}')
if lh.data:
    print("Columns:", list(lh.data[0].keys()))

print()
print("=== CHALLENGE_PARTICIPANTS ===")
pa = supabase.table("challenge_participants").select("*").execute()
print(f'Participants: {len(pa.data or [])}')
