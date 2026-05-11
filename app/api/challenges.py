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

class UpdateProgressRequest(BaseModel):
    user_id: str
    total_points: Optional[int] = None
    current_streak: Optional[int] = None
    progress: Optional[int] = None

PREMIUM_CHALLENGE_TITLE = "Maraton de Productividad"

SEED_CHALLENGES = [
    {
        "title": "Desafio Salud Total",
        "description": "30 dias de habitos saludables: ejercicio, alimentacion consciente y buen descanso. Transforma tu cuerpo y mente.",
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
        "title": PREMIUM_CHALLENGE_TITLE,
        "description": "30 dias de maxima productividad. Despierta temprano, organiza tu dia y cumple tus objetivos sin excusas.",
        "category": "PRODUCTIVIDAD",
        "difficulty": "extreme",
        "duration_days": 30,
        "max_participants": 1000,
        "reward": "?? Badge Productividad Extrema",
        "is_premium_required": True,
        "is_public": True,
        "is_live": True,
        "is_active": True,
        "start_date": datetime.utcnow().isoformat(),
    },
    {
        "title": "Reto Fitness 30",
        "description": "Ejercitate al menos 30 minutos cada dia durante 30 dias. Sin dias de descanso, sin excusas.",
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
        "title": "Desafio Mindfulness",
        "description": "Medita al menos 10 minutos cada dia y registra tu reflexion. Conecta con tu interior durante 30 dias.",
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
        "title": "Reto Conexion Social",
        "description": "Fortaleces tus vinculos. Contacta a alguien, envia un mensaje positivo o participa en comunidad cada dia.",
        "category": "SOCIAL",
        "difficulty": "easy",
        "duration_days": 30,
        "max_participants": 1000,
        "reward": "?? Badge Conexion Social",
        "is_premium_required": False,
        "is_public": True,
        "is_live": True,
        "is_active": True,
        "start_date": datetime.utcnow().isoformat(),
    },
    {
        "title": "Comparte la App con tus Contactos",
        "description": "Invita a 10 amigos a usar Habitly. Comparte el enlace y gana 1 mes Premium gratis.",
        "category": "SOCIAL",
        "difficulty": "easy",
        "duration_days": 30,
        "max_participants": 9999,
        "reward": "?? 1 Mes Premium Gratis",
        "is_premium_required": False,
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
        existing = supabase.table("challenges").select("title,is_premium_required").execute()
        existing_by_title = {c["title"]: c for c in (existing.data or [])}
        inserted = 0
        updated = 0
        for c in SEED_CHALLENGES:
            existing_challenge = existing_by_title.get(c["title"])
            if existing_challenge is None:
                supabase.table("challenges").insert(c).execute()
                inserted += 1
            elif existing_challenge.get("is_premium_required") != c["is_premium_required"]:
                supabase.table("challenges").update({"is_premium_required": c["is_premium_required"]}).eq("title", c["title"]).execute()
                updated += 1
        if inserted or updated:
            print(f"? {inserted} insertados, {updated} actualizados")
        else:
            print("? Todo sincronizado")
    except Exception as e:
        print(f"?? Seed error: {e}")

def is_valid_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False

def _add_participant_count(challenge: dict) -> dict:
    """Add participant count to a challenge dict."""
    try:
        count_resp = supabase.table("challenge_participants").select("id").eq("challenge_id", challenge["id"]).execute()
        challenge["participants_count"] = len(count_resp.data) if count_resp.data else 0
    except Exception:
        challenge["participants_count"] = 0
    challenge.setdefault("is_live", True)
    challenge.setdefault("is_active", True)
    return challenge

@router.get("")
async def get_challenges():
    if not supabase:
        return []
    response = supabase.table("challenges").select("*").order("created_at", desc=True).execute()
    challenges = response.data if response.data else []
    return [_add_participant_count(c) for c in challenges]

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
    return _add_participant_count(challenge)

@router.post("/join")
async def join_challenge(request: JoinChallengeRequest):
    if not supabase:
        return {"id": f"participant-{request.user_id}", "challenge_id": request.challenge_id, "user_id": request.user_id, "user_name": request.user_name}
    if not is_valid_uuid(request.challenge_id) or not is_valid_uuid(request.user_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")
    try:
        challenge_resp = supabase.table("challenges").select("is_premium_required").eq("id", request.challenge_id).execute()
        if challenge_resp.data:
            is_premium_required = challenge_resp.data[0].get("is_premium_required", False)
            if is_premium_required and not request.is_premium:
                raise HTTPException(status_code=403, detail="Este desafio requiere suscripcion Premium")
        
        # Check if already joined
        existing = supabase.table("challenge_participants").select("*").eq("challenge_id", request.challenge_id).eq("user_id", request.user_id).execute()
        if existing.data:
            print(f"User {request.user_id} already joined challenge {request.challenge_id}")
            return existing.data[0]
        
        # Insert new participant - use select() to return the inserted data
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
        print(f"Inserting participant: {data}")
        response = supabase.table("challenge_participants").insert(data).execute()
        print(f"Insert response: {response.data}")
        
        if response.data:
            return response.data[0]
        else:
            # Fallback: fetch the inserted data
            inserted = supabase.table("challenge_participants").select("*").eq("challenge_id", request.challenge_id).eq("user_id", request.user_id).execute()
            if inserted.data:
                return inserted.data[0]
            return data
    except Exception as e:
        print(f"Error joining challenge: {e}")
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

@router.patch("/{challenge_id}/progress")
async def update_progress(challenge_id: str, request: UpdateProgressRequest):
    if not supabase:
        return {"success": True}
    if not is_valid_uuid(challenge_id) or not is_valid_uuid(request.user_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")
    try:
        update_data = {}
        if request.total_points is not None:
            update_data["total_points"] = request.total_points
        if request.current_streak is not None:
            update_data["current_streak"] = request.current_streak
        if request.progress is not None:
            update_data["progress"] = request.progress
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")

        response = supabase.table("challenge_participants").update(update_data).eq("challenge_id", challenge_id).eq("user_id", request.user_id).execute()
        if response.data:
            return response.data[0]
        raise HTTPException(status_code=404, detail="Participant not found")
    except HTTPException:
        raise
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