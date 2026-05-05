from fastapi import APIRouter, HTTPException, Query, Body
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import uuid
from app.database import supabase

router = APIRouter()

class JoinChallengeRequest(BaseModel):
    challenge_id: str
    user_id: str
    user_name: str
    is_premium: bool = False

class LeaveChallengeRequest(BaseModel):
    challenge_id: str
    user_id: str

SEED_CHALLENGES = [
    {
        "title": "Desafío Salud Total",
        "description": "30 días de hábitos saludables",
        "category": "SALUD",
        "difficulty": "hard",
        "duration_days": 30,
        "max_participants": 1000,
        "reward": "?? Premium Gratis 1 Mes",
        "is_premium_required": False,
        "is_public": True,
        "is_live": True,
        "is_active": True,
        "start_date": datetime.utcnow().isoformat(),
    },
    {
        "title": "Maratón de Productividad",
        "description": "30 días de máxima productividad",
        "category": "PRODUCTIVIDAD",
        "difficulty": "extreme",
        "duration_days": 30,
        "max_participants": 1000,
        "reward": "?? Badge Productividad Extrema",
        "is_premium_required": False,
        "is_public": True,
        "is_live": True,
        "is_active": True,
        "start_date": datetime.utcnow().isoformat(),
    },
    {
        "title": "Reto Fitness 30",
        "description": "Ejercítate 30 min cada día",
        "category": "EJERCICIO",
        "difficulty": "hard",
        "duration_days": 30,
        "max_participants": 500,
        "reward": "?? Badge Guerrero Fitness",
        "is_premium_required": False,
        "is_public": True,
        "is_live": True,
        "is_active": True,
        "start_date": datetime.utcnow().isoformat(),
    },
    {
        "title": "Desafío Mindfulness",
        "description": "Medita 10 minutos cada día",
        "category": "MINDFULNESS",
        "difficulty": "medium",
        "duration_days": 30,
        "max_participants": 1000,
        "reward": "?? Badge Calma Interior",
        "is_premium_required": False,
        "is_public": True,
        "is_live": True,
        "is_active": True,
        "start_date": datetime.utcnow().isoformat(),
    },
    {
        "title": "Reto Conexión Social",
        "description": "Fortalece tus vínculos",
        "category": "SOCIAL",
        "difficulty": "easy",
        "duration_days": 30,
        "max_participants": 1000,
        "reward": "?? Badge Conexión Social",
        "is_premium_required": False,
        "is_public": True,
        "is_live": True,
        "is_active": True,
        "start_date": datetime.utcnow().isoformat(),
    },
    {
        "title": "Desafío Premium Élite",
        "description": "SOLO PREMIUM: El reto definitivo",
        "category": "SALUD",
        "difficulty": "extreme",
        "duration_days": 30,
        "max_participants": 100,
        "reward": "?? 1 AÑO PREMIUM GRATIS",
        "is_premium_required": True,
        "is_public": True,
        "is_live": True,
        "is_active": True,
        "start_date": datetime.utcnow().isoformat(),
    },
    {
        "title": "Desafío Titán Extremo",
        "description": "EXCLUSIVO PREMIUM: 45 días de entrenamiento militar, dieta estricta y meditación avanzada. Solo para guerreros.",
        "category": "SALUD",
        "difficulty": "extreme",
        "duration_days": 45,
        "max_participants": 50,
        "reward": "?????? Titán Habitly + 2 Años Premium",
        "is_premium_required": True,
        "is_public": True,
        "is_live": True,
        "is_active": True,
        "start_date": datetime.utcnow().isoformat(),
    },
]

def seed_challenges_on_startup():
    if not supabase:
        return
    try:
        existing = supabase.table("challenges").select("id").limit(1).execute()
        if existing.data:
            return
        for c in SEED_CHALLENGES:
            supabase.table("challenges").insert(c).execute()
        print("? 7 desafíos iniciales creados")
    except Exception as e:
        print(f"?? Seed error: {e}")

def is_valid_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False

@router.get("")
async def get_challenges():
    if not supabase:
        return []
    response = supabase.table("challenges").select("*").order("created_at", desc=True).execute()
    challenges = response.data if response.data else []
    for c in challenges:
        c.setdefault("is_live", True)
        c.setdefault("is_active", True)
    return challenges

@router.get("/{challenge_id}")
async def get_challenge(challenge_id: str):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase no configurado")
    if not is_valid_uuid(challenge_id):
        raise HTTPException(status_code=400, detail="Invalid challenge ID format")
    response = supabase.table("challenges").select("*").eq("id", challenge_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Challenge not found")
    challenge = response.data[0]
    challenge.setdefault("is_live", True)
    challenge.setdefault("is_active", True)
    return challenge

@router.post("/join")
async def join_challenge(request: JoinChallengeRequest):
    if not supabase:
        return {"id": f"participant-{request.user_id}", "challenge_id": request.challenge_id, "user_id": request.user_id}
    if not is_valid_uuid(request.challenge_id) or not is_valid_uuid(request.user_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")
    try:
        challenge_resp = supabase.table("challenges").select("is_premium_required").eq("id", request.challenge_id).execute()
        if challenge_resp.data:
            is_premium_required = challenge_resp.data[0].get("is_premium_required", False)
            if is_premium_required and not request.is_premium:
                raise HTTPException(status_code=403, detail="Este desafío requiere suscripción Premium")
        existing = supabase.table("challenge_participants").select("*").eq("challenge_id", request.challenge_id).eq("user_id", request.user_id).execute()
        if existing.data:
            return existing.data[0]
        data = {
            "challenge_id": request.challenge_id,
            "user_id": request.user_id,
            "user_name": request.user_name,
            "joined_at": datetime.utcnow().isoformat(),
            "progress": 0,
            "current_streak": 0,
            "best_streak": 0,
            "total_points": 0
        }
        response = supabase.table("challenge_participants").insert(data).execute()
        return response.data[0] if response.data else data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.post("/leave")
async def leave_challenge(request: LeaveChallengeRequest):
    if not supabase:
        return {"success": True}
    if not is_valid_uuid(request.challenge_id) or not is_valid_uuid(request.user_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")
    try:
        response = supabase.table("challenge_participants").delete().eq("challenge_id", request.challenge_id).eq("user_id", request.user_id).execute()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/{challenge_id}/participants")
async def get_participants(challenge_id: str):
    if not supabase:
        return []
    if not is_valid_uuid(challenge_id):
        raise HTTPException(status_code=400, detail="Invalid challenge ID format")
    try:
        response = supabase.table("challenge_participants").select("*").eq("challenge_id", challenge_id).execute()
        return response.data if response.data else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")