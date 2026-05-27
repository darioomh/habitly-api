from app.database import supabase

print("=== CURRENT CHALLENGES ===")
r = supabase.table("challenges").select("id,title,category,is_premium_required,status").execute()
for c in (r.data or []):
    print(f'{c["id"][:8]} | cat={c["category"]:14s} | premium={c["is_premium_required"]} | status={c.get("status")} | {c["title"]}')

print()
print("=== HABITS ===")
hr = supabase.table("habits").select("id,category,title").execute()
print(f'Total: {len(hr.data or [])}')
cats = {}
for h in (hr.data or []):
    cat = h["category"] or "NONE"
    if cat not in cats:
        cats[cat] = []
    cats[cat].append(h["title"])
for cat, habits in sorted(cats.items()):
    print(f'  {cat}: {len(habits)} habits')
    for t in habits:
        print(f'    - {t}')

print()
print("=== CHALLENGE_HABITS LINKS ===")
lr = supabase.table("challenge_habits").select("id,challenge_id,habit_id").execute()
print(f'Links: {len(lr.data or [])}')

print()
print("=== CHALLENGE PARTICIPANTS ===")
pr = supabase.table("challenge_participants").select("id,challenge_id,user_id").execute()
print(f'Participants: {len(pr.data or [])}')
