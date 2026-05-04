from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime
from app.database import supabase
from app.models.models import Habit, HabitCreate

router = APIRouter()

@router.get("")
async def get_habits(
    user_id: str = Query(..., description="ID del usuario"),
    is_active: Optional[bool] = True
):
    """Get all habits for a user"""
    if not supabase:
        return []
    
    query = supabase.table("habits").select("*").eq("user_id", user_id)
    if is_active is not None:
        query = query.eq("is_active", is_active)
    
    response = query.order("created_at", desc=True).execute()
    return response.data if response.data else []

@router.get("/{habit_id}")
async def get_habit(habit_id: str):
    """Get a single habit"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase no configurado")
    
    response = supabase.table("habits").select("*").eq("id", habit_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Habit not found")
    return response.data[0]

@router.post("")
async def create_habit(habit: HabitCreate):
    """Create a new habit"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase no configurado")
    
    data = habit.model_dump()
    data["created_at"] = datetime.utcnow().isoformat()
    data["updated_at"] = datetime.utcnow().isoformat()
    
    response = supabase.table("habits").insert(data).execute()
    if response.error:
        raise HTTPException(status_code=500, detail=response.error.message)
    return response.data[0]

@router.put("/{habit_id}")
async def update_habit(habit_id: str, title: Optional[str] = None, description: Optional[str] = None):
    """Update a habit"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase no configurado")
    
    data = {"updated_at": datetime.utcnow().isoformat()}
    if title:
        data["title"] = title
    if description:
        data["description"] = description
    
    response = supabase.table("habits").update(data).eq("id", habit_id).execute()
    if response.error:
        raise HTTPException(status_code=500, detail=response.error.message)
    if not response.data:
        raise HTTPException(status_code=404, detail="Habit not found")
    return response.data[0]

@router.delete("/{habit_id}")
async def delete_habit(habit_id: str):
    """Soft delete a habit"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase no configurado")
    
    response = supabase.table("habits").update({"is_active": False}).eq("id", habit_id).execute()
    if response.error:
        raise HTTPException(status_code=500, detail=response.error.message)
    return {"success": True}

@router.post("/logs")
async def create_habit_log(
    habit_id: str,
    user_id: str,
    date: str,
    completed: bool = False,
    notes: Optional[str] = None
):
    """Log habit completion"""
    if not supabase:
        return {"id": f"log-{habit_id}-{date}", "habit_id": habit_id, "completed": completed}
    
    data = {
        "habit_id": habit_id,
        "user_id": user_id,
        "date": date,
        "completed": completed,
        "notes": notes,
        "xp_earned": 10 if completed else 0,
        "created_at": datetime.utcnow().isoformat()
    }
    
    # Check if exists
    existing = supabase.table("habit_logs").select("*").eq("habit_id", habit_id).eq("date", date).execute()
    
    if existing.data:
        response = supabase.table("habit_logs").update(data).eq("id", existing.data[0]["id"]).execute()
    else:
        response = supabase.table("habit_logs").insert(data).execute()
    
    return response.data[0] if response.data else data

@router.get("/logs/{habit_id}")
async def get_habit_logs(habit_id: str):
    """Get logs for a habit"""
    if not supabase:
        return []
    
    response = supabase.table("habit_logs").select("*").eq("habit_id", habit_id).order("date", desc=True).execute()
    return response.data if response.data else []