from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timezone
import os
import httpx
from app.database import supabase
from app.models.models import JournalEntry, JournalEntryCreate, JournalListResponse

router = APIRouter()

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS journal_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    mood TEXT NOT NULL,
    note TEXT,
    habit_reflections JSONB DEFAULT '[]',
    notes JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, date)
);
CREATE INDEX IF NOT EXISTS idx_journal_entries_user_id ON journal_entries(user_id);
CREATE INDEX IF NOT EXISTS idx_journal_entries_date ON journal_entries(date);
"""

ADD_NOTES_COLUMN_SQL = "ALTER TABLE journal_entries ADD COLUMN IF NOT EXISTS notes JSONB DEFAULT '[]';"

BACKFILL_NOTES_SQL = """
UPDATE journal_entries SET notes = CASE
    WHEN note IS NOT NULL AND note != '' THEN
        jsonb_build_array(jsonb_build_object('text', note, 'created_at', COALESCE(updated_at, created_at)))
    ELSE '[]'::jsonb
END WHERE notes IS NULL OR notes = '[]'::jsonb;
"""

RELOAD_SCHEMA_SQL = "NOTIFY pgrst, 'reload schema';"


def _run_sql(sql: str, url: str, key: str, label: str):
    try:
        r = httpx.post(
            f"{url}/sql",
            json={"query": sql},
            headers={
                "apikey": key,
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            timeout=15,
        )
        if r.status_code == 200:
            print(f"{label}: OK")
        else:
            print(f"{label} warning ({r.status_code}): {r.text[:200]}")
    except Exception as e:
        print(f"{label} error: {e}")


def migrate_journal_table():
    """Ensure journal_entries table has all columns, on startup."""
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_KEY", "")
    if not url or not key:
        print("WARNING: Supabase not configured, skipping journal migration.")
        return
    _run_sql(CREATE_TABLE_SQL, url, key, "Journal table")
    _run_sql(ADD_NOTES_COLUMN_SQL, url, key, "Add notes column")
    _run_sql(BACKFILL_NOTES_SQL, url, key, "Backfill notes")
    _run_sql(RELOAD_SCHEMA_SQL, url, key, "Reload PostgREST schema")

@router.get("")
async def get_journal_entry(user_id: str = Query(...), date: str = Query(...)):
    """Get journal entry for a specific date"""
    if not supabase:
        return {"id": None, "user_id": user_id, "date": date, "mood": "", "note": None, "habit_reflections": None, "notes": []}
    try:
        response = supabase.table("journal_entries").select("*").eq("user_id", user_id).eq("date", date).execute()
        if not response.data:
            return {"id": None, "user_id": user_id, "date": date, "mood": "", "note": None, "habit_reflections": None, "notes": []}
        return response.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/range")
async def get_journal_entries(user_id: str = Query(...), from_date: str = Query(alias="from"), to: str = Query(...)):
    """Get journal entries in a date range"""
    if not supabase:
        return {"entries": []}
    try:
        response = (
            supabase.table("journal_entries")
            .select("*")
            .eq("user_id", user_id)
            .gte("date", from_date)
            .lte("date", to)
            .order("date", desc=True)
            .execute()
        )
        return {"entries": response.data if response.data else []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("")
async def save_journal_entry(entry: JournalEntryCreate):
    """Create or update a journal entry. Appends note to notes array instead of replacing."""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")

    now = datetime.now(timezone.utc).isoformat()
    data = entry.model_dump(exclude_none=True)
    data["updated_at"] = now

    # Build the new note entry to append
    new_note_entry = None
    if entry.note and entry.note.strip():
        new_note_entry = {"text": entry.note.strip(), "created_at": now}

    def _try_save(data_to_save):
        existing = supabase.table("journal_entries").select("*").eq("user_id", entry.user_id).eq("date", entry.date).execute()
        if existing.data:
            existing_row = existing.data[0]
            return supabase.table("journal_entries").update(data_to_save).eq("id", existing_row["id"]).execute()
        else:
            data_to_save["created_at"] = now
            return supabase.table("journal_entries").insert(data_to_save).execute()

    try:
        existing = supabase.table("journal_entries").select("*").eq("user_id", entry.user_id).eq("date", entry.date).execute()
        if existing.data:
            existing_row = existing.data[0]
            existing_notes = existing_row.get("notes") or []
            if new_note_entry:
                existing_notes.append(new_note_entry)
            data["notes"] = existing_notes
            if new_note_entry:
                data["note"] = new_note_entry["text"]
            response = supabase.table("journal_entries").update(data).eq("id", existing_row["id"]).execute()
        else:
            data["created_at"] = now
            if new_note_entry:
                data["notes"] = [new_note_entry]
                data["note"] = new_note_entry["text"]
            else:
                data["notes"] = []
            response = supabase.table("journal_entries").insert(data).execute()
        return response.data[0]
    except Exception as e:
        detail = str(e)
        if "notes" in detail.lower() and "column" in detail.lower():
            # notes column doesn't exist yet, save without it
            data.pop("notes", None)
            try:
                response = _try_save(data)
                return response.data[0]
            except Exception as e2:
                raise HTTPException(status_code=500, detail=str(e2))
        if "violates foreign key constraint" in detail.lower():
            raise HTTPException(status_code=400, detail="User not found. Please create an account first.")
        if "duplicate key value" in detail.lower():
            raise HTTPException(status_code=409, detail="Entry already exists for this date.")
        raise HTTPException(status_code=500, detail=detail)

@router.delete("/{entry_id}")
async def delete_journal_entry(entry_id: str):
    """Delete a journal entry"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    try:
        response = supabase.table("journal_entries").delete().eq("id", entry_id).execute()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
