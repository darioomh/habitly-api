from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from datetime import datetime, timezone
from app.database import supabase
from app.auth import get_current_user

router = APIRouter()

DEFAULT_SETTINGS = {
    "theme": "system",
    "notifications": True,
    "reminder_time": "09:00",
    "sync_enabled": True
}


@router.get("/me")
async def get_me_settings(user_id: str = Depends(get_current_user)):
    if not supabase:
        return dict(DEFAULT_SETTINGS)

    response = supabase.table("user_preferences").select("*").eq("user_id", user_id).execute()
    if response.data:
        row = response.data[0]
        return {
            "theme": row.get("theme") or "system",
            "notifications": row.get("notifications", True),
            "reminder_time": row.get("reminder_time") or "09:00",
            "sync_enabled": row.get("sync_enabled", True),
        }
    return dict(DEFAULT_SETTINGS)


@router.put("/me")
async def update_me_settings(
    theme: Optional[str] = None,
    notifications: Optional[bool] = None,
    reminder_time: Optional[str] = None,
    sync_enabled: Optional[bool] = None,
    user_id: str = Depends(get_current_user)
):
    if not supabase:
        return {"success": True}

    data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if theme:
        data["theme"] = theme
    if notifications is not None:
        data["notifications"] = notifications
    if reminder_time:
        data["reminder_time"] = reminder_time
    if sync_enabled is not None:
        data["sync_enabled"] = sync_enabled

    existing = supabase.table("user_preferences").select("id").eq("user_id", user_id).execute()

    if existing.data:
        response = supabase.table("user_preferences").update(data).eq("user_id", user_id).execute()
    else:
        data["user_id"] = user_id
        data["created_at"] = datetime.now(timezone.utc).isoformat()
        response = supabase.table("user_preferences").insert(data).execute()

    return response.data[0] if response.data else {"success": True}


@router.post("/sync-status")
async def sync_status(user_id: str = Depends(get_current_user)):
    return {"synced_at": datetime.now(timezone.utc).isoformat(), "status": "success"}
