from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
from typing import Optional, List
import uuid
from app.database import supabase

router = APIRouter()

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
    return response.data[0]

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
    user_name: str
):
    """Join a challenge"""
    if not supabase:
        return {"id": f"participant-{user_id}", "challenge_id": challenge_id, "user_id": user_id}
    
    if not is_valid_uuid(challenge_id) or not is_valid_uuid(user_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")
    
    try:
        # Check if already joined
        existing = supabase.table("challenge_participants").select("*").eq("challenge_id", challenge_id).eq("user_id", user_id).execute()
        
        if existing.data:
            return existing.data[0]
        
        data = {
            "challenge_id": challenge_id,
            "user_id": user_id,
            "joined_at": datetime.utcnow().isoformat(),
            "progress": 0
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
async def update_progress(challenge_id: str, user_id: str, progress: int):
    """Update user progress in a challenge"""
    if not supabase:
        return {"success": True}
    
    if not is_valid_uuid(challenge_id) or not is_valid_uuid(user_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")
    
    try:
        response = supabase.table("challenge_participants").update({"progress": progress}).eq("challenge_id", challenge_id).eq("user_id", user_id).execute()
        return response.data[0] if response.data else {"success": True, "progress": progress}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
