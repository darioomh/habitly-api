from fastapi import APIRouter, HTTPException, Body, Depends
from datetime import datetime, timedelta
from typing import Any, Dict, List
import uuid
from app.database import supabase
from app.auth import get_current_user

router = APIRouter()

FLASH_SEEDS = [
    ("flash-no-sugar-48h", "0 azucar", "48 horas sin bebidas azucaradas ni dulces procesados.", 48, "SALUD", "medium", 90),
    ("flash-steps-10k", "10k pasos hoy", "Cierra el dia con 10.000 pasos y una caminata consciente.", 24, "EJERCICIO", "hard", 120),
    ("flash-no-tiktok-24h", "Sin TikTok", "24 horas sin scroll infinito. Recupera atencion profunda.", 24, "PRODUCTIVIDAD", "medium", 80),
    ("flash-sleep-72h", "Dormir 8h x 3", "Tres noches seguidas priorizando descanso real.", 72, "SALUD", "hard", 160),
]

def _valid_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
        return True
    except Exception:
        return False

def _seed_payload(user_id: str | None = None) -> List[Dict[str, Any]]:
    now = datetime.utcnow()
    return [
        {
            "id": item[0],
            "title": item[1],
            "description": item[2],
            "duration_hours": item[3],
            "category": item[4],
            "difficulty": item[5],
            "xp_reward": item[6],
            "participants_count": 0,
            "starts_at": (now - timedelta(hours=2)).isoformat(),
            "ends_at": (now + timedelta(hours=item[3] - 2)).isoformat(),
            "is_joined": False,
        }
        for item in FLASH_SEEDS
    ]

@router.get("")
async def get_flash_challenges(user_id: str | None = None):
    if not supabase:
        return _seed_payload(user_id)
    try:
        response = supabase.table("flash_challenges").select("*").eq("is_active", True).execute()
        rows = response.data or []
        result = []
        for row in rows:
            count = supabase.table("flash_participants").select("id").eq("flash_challenge_id", row["id"]).execute()
            joined = False
            if user_id:
                joined_resp = (
                    supabase.table("flash_participants")
                    .select("id")
                    .eq("flash_challenge_id", row["id"])
                    .eq("user_id", user_id)
                    .execute()
                )
                joined = bool(joined_resp.data)
            row["participants_count"] = len(count.data or [])
            row["is_joined"] = joined
            result.append(row)
        return result if result else _seed_payload(user_id)
    except Exception:
        return _seed_payload(user_id)

@router.post("/{flash_id}/join")
async def join_flash_challenge(flash_id: str, payload: Dict[str, Any] = Body(...), user_id: str = Depends(get_current_user)):
    user_name = payload.get("user_name") or user_id
    if not supabase:
        item = next((x for x in _seed_payload(user_id) if x["id"] == flash_id), None)
        if not item:
            raise HTTPException(status_code=404, detail="Flash challenge not found")
        item["is_joined"] = True
        item["participants_count"] += 1
        return item
    if not _valid_uuid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    try:
        existing = (
            supabase.table("flash_participants")
            .select("*")
            .eq("flash_challenge_id", flash_id)
            .eq("user_id", user_id)
            .execute()
        )
        if not existing.data:
            supabase.table("flash_participants").insert({
                "flash_challenge_id": flash_id,
                "user_id": user_id,
                "user_name": user_name,
                "joined_at": datetime.utcnow().isoformat(),
            }).execute()
        challenges = await get_flash_challenges(user_id)
        item = next((x for x in challenges if x["id"] == flash_id), None)
        if not item:
            raise HTTPException(status_code=404, detail="Flash challenge not found")
        return item
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.post("/{flash_id}/share")
async def share_flash_challenge(flash_id: str, payload: Dict[str, Any] = Body(...), user_id: str = Depends(get_current_user)):
    if not supabase:
        item = next((x for x in _seed_payload(user_id) if x["id"] == flash_id), None)
        if not item:
            raise HTTPException(status_code=404, detail="Flash challenge not found")
        return item
    if not _valid_uuid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    try:
        supabase.table("flash_shares").insert({
            "flash_challenge_id": flash_id,
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
        }).execute()
        challenges = await get_flash_challenges(user_id)
        return next((x for x in challenges if x["id"] == flash_id), None)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
