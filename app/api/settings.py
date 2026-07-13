from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from app.database import supabase
from app.auth import get_current_user

router = APIRouter()

@router.get("/me")
async def get_me_settings(user_id: str = Depends(get_current_user)):
    return {
        "theme": "system",
        "notifications": True,
        "reminder_time": "09:00",
        "sync_enabled": True
    }

@router.put("/me")
async def update_me_settings(
    theme: Optional[str] = None,
    notifications: Optional[bool] = None,
    user_id: str = Depends(get_current_user)
):
    return {"success": True}

@router.post("/sync-status")
async def sync_status(user_id: str = Depends(get_current_user)):
    return {"synced_at": "2024-01-01T00:00:00", "status": "success"}
