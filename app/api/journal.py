from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timezone
from app.database import supabase
from app.models.models import JournalEntry, JournalEntryCreate, JournalListResponse

router = APIRouter()

@router.get("")
async def get_journal_entry(user_id: str = Query(...), date: str = Query(...)):
    """Get journal entry for a specific date"""
    if not supabase:
        return {"id": None, "user_id": user_id, "date": date, "mood": "", "note": None, "habit_reflections": None}
    try:
        response = supabase.table("journal_entries").select("*").eq("user_id", user_id).eq("date", date).execute()
        if not response.data:
            return {"id": None, "user_id": user_id, "date": date, "mood": "", "note": None, "habit_reflections": None}
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
    """Create or update a journal entry"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")

    now = datetime.now(timezone.utc).isoformat()
    data = entry.model_dump(exclude_none=True)
    data["updated_at"] = now

    try:
        existing = supabase.table("journal_entries").select("*").eq("user_id", entry.user_id).eq("date", entry.date).execute()
        if existing.data:
            response = supabase.table("journal_entries").update(data).eq("id", existing.data[0]["id"]).execute()
        else:
            data["created_at"] = now
            response = supabase.table("journal_entries").insert(data).execute()
        return response.data[0]
    except Exception as e:
        detail = str(e)
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
