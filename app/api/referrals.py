from fastapi import APIRouter, HTTPException, Body, Depends
from datetime import datetime
from typing import Any, Dict
import uuid
from app.database import supabase
from app.auth import get_current_user

router = APIRouter()
TARGET_INVITES = 10

def _valid_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
        return True
    except Exception:
        return False

def _fallback(user_id: str, invite_count: int = 0) -> Dict[str, Any]:
    code = user_id[-8:].upper() if user_id else "DEMO0000"
    return {
        "user_id": user_id,
        "referral_code": code,
        "invite_count": invite_count,
        "target_invites": TARGET_INVITES,
        "is_premium_unlocked": invite_count >= TARGET_INVITES,
        "referral_url": f"https://habitly.app/r/{code}",
    }

@router.get("/me")
async def get_me_referral_progress(user_id: str = Depends(get_current_user)):
    if not supabase:
        return _fallback(user_id)
    response = supabase.table("referral_progress").select("*").eq("user_id", user_id).execute()
    if response.data:
        return response.data[0]
    data = _fallback(user_id)
    inserted = supabase.table("referral_progress").insert({
        **data,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }).execute()
    return inserted.data[0] if inserted.data else data

@router.post("/share")
async def track_referral_share(payload: Dict[str, Any] = Body(...), user_id: str = Depends(get_current_user)):
    if not supabase:
        return _fallback(user_id, 1)
    current = await get_me_referral_progress(user_id)
    invite_count = int(current.get("invite_count") or 0) + 1
    premium = invite_count >= TARGET_INVITES
    update = {
        "invite_count": invite_count,
        "is_premium_unlocked": premium,
        "updated_at": datetime.utcnow().isoformat(),
    }
    response = supabase.table("referral_progress").update(update).eq("user_id", user_id).execute()
    if premium:
        try:
            supabase.table("users").update({"is_premium": True}).eq("id", user_id).execute()
        except Exception:
            pass
    return response.data[0] if response.data else {**current, **update}
