from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import uuid
from app.database import supabase

router = APIRouter()

SEED_CHALLENGES = [
    {
        "title": "Desafío Salud Total",
        "description": "30 días de hábitos saludables: ejercicio, alimentación consciente y buen descanso. Transforma tu cuerpo y mente.",
        "category": "SALUD",
        "difficulty": "hard",
        "duration_days": 30,
        "max_participants": 1000,
        "reward": "🏆 Premium Gratis 1 Mes",
        "is_premium_required": False,
        "is_public": True,
        "start_date": datetime.utcnow().isoformat(),
    },
    {
        "title": "Maratón de Productividad",
        "description": "30 días de máxima productividad. Despierta temprano, organiza tu día y cumple tus objetivos sin excusas.",
        "category": "PRODUCTIVIDAD",
        "difficulty": "extreme",
        "duration_days": 30,
        "max_participants": 1000,
        "reward": "💎 Badge Productividad Extrema",
        "is_premium_required": False,
        "is_public": True,
        "start_date": datetime.utcnow().isoformat(),
    },
    {
        "title": "Reto Fitness 30",
        "description": "Ejercítate al menos 30 minutos cada día durante 30 días. Sin días de descanso, sin excusas.",
        "category": "EJERCICIO",
        "difficulty": "hard",
        "duration_days": 30,
        "max_participants": 500,
        "reward": "💪 Badge Guerrero Fitness",
        "is_premium_required": False,
        "is_public": True,
        "start_date": datetime.utcnow().isoformat(),
    },
    {
        "title": "Desafío Mindfulness",
        "description": "Medita al menos 10 minutos cada día y registra tu reflexión. Conecta con tu interior durante 30 días.",
        "category": "MINDFULNESS",
        "difficulty": "medium",
        "duration_days": 30,
        "max_participants": 1000,
        "reward": "🧘 Badge Calma Interior",
        "is_premium_required": False,
        "is_public": True,
        "start_date": datetime.utcnow().isoformat(),
    },
    {
        "title": "Reto Conexión Social",
        "description": "Fortalece tus vínculos. Contacta a alguien, envía un mensaje positivo o participa en comunidad cada día.",
        "category": "SOCIAL",
        "difficulty": "easy",
        "duration_days": 30,
        "max_participants": 1000,
        "reward": "🤝 Badge Conexión Social",
        "is_premium_required": False,
        "is_public": True,
        "start_date": datetime.utcnow().isoformat(),
    },
    {
        "title": "Desafío Premium Élite",
        "description": "SOLO PREMIUM: El reto definitivo. 30 días de exigencia máxima. El ganador recibe 1 AÑO DE PREMIUM GRATIS.",
        "category": "SALUD",
        "difficulty": "extreme",
        "duration_days": 30,
        "max_participants": 100,
        "reward": "👑 1 AÑO PREMIUM GRATIS",
        "reward_description": "El primer lugar del ranking recibe 1 año de suscripción Premium gratis",
        "is_premium_required": True,
        "is_public": True,
        "start_date": datetime.utcnow().isoformat(),
    },
]


def seed_challenges_on_startup():
    """Insert 6 initial challenges if table is empty."""
    if not supabase:
        return
    try:
        existing = supabase.table("challenges").select("id").limit(1).execute()
        if existing.data:
            return
        for c in SEED_CHALLENGES:
            supabase.table("challenges").insert(c).execute()
        print("✅ 6 desafíos iniciales creados")
    except Exception as e:
        print(f"⚠️ Seed error: {e}")

def is_valid_uuid(value: str) -> bool:
    """Check if a string is a valid UUID"""
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False

@router.get("")
async def get_challenges():
    """Get all challenges"""
    if not supabase:
        return []
    
    response = supabase.table("challenges").select("*").order("created_at", desc=True).execute()
    return response.data if response.data else []

@router.get("/{challenge_id}")
async def get_challenge(challenge_id: str):
    """Get a single challenge"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase no configurado")
    
    if not is_valid_uuid(challenge_id):
        raise HTTPException(status_code=400, detail="Invalid challenge ID format")
    
    response = supabase.table("challenges").select("*").eq("id", challenge_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    challenge = response.data[0]
    # Check if challenge has ended and needs winner declaration
    if challenge.get("end_date"):
        end_date = datetime.fromisoformat(challenge["end_date"].replace("Z", "+00:00"))
        if datetime.utcnow() > end_date:
            if challenge.get("status") == "active":
                await declare_winners(challenge_id)
                # Re-fetch after declaring winners
                response = supabase.table("challenges").select("*").eq("id", challenge_id).execute()
                challenge = response.data[0] if response.data else challenge
    
    return challenge

async def declare_winners(challenge_id: str):
    """Declare winners for a completed challenge"""
    try:
        # Get challenge details
        challenge_resp = supabase.table("challenges").select("*").eq("id", challenge_id).execute()
        if not challenge_resp.data:
            return {"error": "Challenge not found"}
        
        challenge = challenge_resp.data[0]
        is_premium = challenge.get("is_premium_required", False)
        
        # Get all participants sorted by progress (streak)
        participants_resp = supabase.table("challenge_participants").select("*").eq("challenge_id", challenge_id).order("current_streak", desc=True).execute()
        participants = participants_resp.data if participants_resp.data else []
        
        if not participants:
            return {"message": "No participants"}
        
        # Mark top 3 as winners
        winners = []
        for i, p in enumerate(participants[:3]):
            winner_data = {
                "rank": i + 1,
                "user_id": p["user_id"],
                "user_name": p.get("user_name", "Anónimo"),
                "current_streak": p.get("current_streak", 0),
                "total_points": p.get("total_points", 0)
            }
            winners.append(winner_data)
            
            # Grant 1 year premium to first place if it's a premium challenge
            if i == 0 and is_premium:
                await grant_premium_year(p["user_id"], challenge_id)
        
        # Save winners to database
        year_month = datetime.utcnow().strftime("%Y-%m")
        winner_record = {
            "challenge_id": challenge_id,
            "year_month": year_month,
            "winners": winners,
            "reward_given": True,
            "reward_given_at": datetime.utcnow().isoformat()
        }
        
        supabase.table("challenge_winners").upsert(winner_record, on_conflict="challenge_id").execute()
        
        # Update challenge status
        supabase.table("challenges").update({"status": "completed"}).eq("id", challenge_id).execute()
        
        return {"winners": winners, "is_premium_challenge": is_premium}
    except Exception as e:
        print(f"Error declaring winners: {e}")
        return {"error": str(e)}

async def grant_premium_year(user_id: str, challenge_id: str):
    """Grant 1 year premium to the winner"""
    try:
        # Update user's premium status in Supabase
        # This assumes you have a user_subscriptions table or similar
        # For now, we'll just log it
        print(f"🏆 Granting 1 year premium to user {user_id} for winning challenge {challenge_id}")
        
        # You could also send a notification, email, etc.
        # Example: Insert into a subscriptions table
        # supabase.table("user_subscriptions").insert({
        #     "user_id": user_id,
        #     "tier": "PREMIUM_YEARLY",
        #     "start_date": datetime.utcnow().isoformat(),
        #     "end_date": (datetime.utcnow() + timedelta(days=365)).isoformat(),
        #     "source": f"challenge_winner_{challenge_id}"
        # }).execute()
        
        return True
    except Exception as e:
        print(f"Error granting premium: {e}")
        return False

@router.post("")
async def create_challenge(
    title: str,
    description: str,
    category: str,
    difficulty: str = "medium",
    duration_days: int = 30,
    creator_id: Optional[str] = None
):
    """Create a new challenge"""
    if not supabase:
        return {"id": f"challenge-{title}", "title": title}
    
    data = {
        "title": title,
        "description": description,
        "category": category,
        "difficulty": difficulty,
        "duration_days": duration_days,
        "creator_id": creator_id,
        "start_date": datetime.utcnow().isoformat()
    }
    
    response = supabase.table("challenges").insert(data).execute()
    return response.data[0] if response.data else data

@router.get("/{challenge_id}/participants")
async def get_participants(challenge_id: str):
    """Get participants for a challenge"""
    if not supabase:
        return []
    
    if not is_valid_uuid(challenge_id):
        raise HTTPException(status_code=400, detail="Invalid challenge ID format")
    
    try:
        response = supabase.table("challenge_participants").select("*").eq("challenge_id", challenge_id).execute()
        return response.data if response.data else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.post("/join")
async def join_challenge(
    challenge_id: str,
    user_id: str,
    user_name: str,
    is_premium: bool = False
):
    """Join a challenge"""
    if not supabase:
        return {"id": f"participant-{user_id}", "challenge_id": challenge_id, "user_id": user_id}
    
    if not is_valid_uuid(challenge_id) or not is_valid_uuid(user_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")
    
    try:
        # Check if challenge requires premium
        challenge_resp = supabase.table("challenges").select("is_premium_required").eq("id", challenge_id).execute()
        if challenge_resp.data:
            is_premium_required = challenge_resp.data[0].get("is_premium_required", False)
            if is_premium_required and not is_premium:
                raise HTTPException(status_code=403, detail="Este desafío requiere suscripción Premium")
        
        # Check if already joined
        existing = supabase.table("challenge_participants").select("*").eq("challenge_id", challenge_id).eq("user_id", user_id).execute()
        
        if existing.data:
            return existing.data[0]
        
        data = {
            "challenge_id": challenge_id,
            "user_id": user_id,
            "user_name": user_name,
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
async def leave_challenge(challenge_id: str, user_id: str):
    """Leave a challenge"""
    if not supabase:
        return {"success": True}
    
    if not is_valid_uuid(challenge_id) or not is_valid_uuid(user_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")
    
    try:
        response = supabase.table("challenge_participants").delete().eq("challenge_id", challenge_id).eq("user_id", user_id).execute()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.put("/{challenge_id}/progress")
async def update_progress(challenge_id: str, user_id: str, progress: int, current_streak: int = 0, best_streak: int = 0):
    """Update user progress in a challenge"""
    if not supabase:
        return {"success": True}
    
    if not is_valid_uuid(challenge_id) or not is_valid_uuid(user_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")
    
    try:
        data = {"progress": progress}
        if current_streak > 0:
            data["current_streak"] = current_streak
        if best_streak > 0:
            data["best_streak"] = best_streak
            
        response = supabase.table("challenge_participants").update(data).eq("challenge_id", challenge_id).eq("user_id", user_id).execute()
        return response.data[0] if response.data else {"success": True, "progress": progress}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.post("/{challenge_id}/declare-winners")
async def declare_winners_endpoint(challenge_id: str):
    """Manually trigger winner declaration"""
    return await declare_winners(challenge_id)

@router.get("/{challenge_id}/winners")
async def get_winners(challenge_id: str):
    """Get winners for a challenge"""
    if not supabase:
        return []
    
    try:
        response = supabase.table("challenge_winners").select("*").eq("challenge_id", challenge_id).execute()
        return response.data if response.data else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/winners")
async def get_all_winners(user_id: Optional[str] = Query(None)):
    """Get all winners or winners for a specific user"""
    if not supabase:
        return []
    
    try:
        query = supabase.table("challenge_winners").select("*")
        if user_id:
            # Filter winners that contain this user_id
            query = query.filter("winners", "cs", f'[{{"user_id": "{user_id}"}}]')
        response = query.order("created_at", desc=True).execute()
        return response.data if response.data else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
