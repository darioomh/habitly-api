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
        response = None

    # Insert or update the habit log
    if existing.data:
        response = supabase.table("habit_logs").update(data).eq("id", existing.data[0]["id"]).execute()
    else:
        response = supabase.table("habit_logs").insert(data).execute()

    result = response.data[0] if response.data else data

    # If completed, award XP to linked challenge participants automatically
    try:
        if completed:
            # Determine xp amount: xp_earned from log or habit.xp_value
            xp_amount = int(result.get("xp_earned") or 0)
            if xp_amount == 0:
                try:
                    habit_resp = supabase.table("habits").select("xp_value").eq("id", habit_id).execute()
                    if habit_resp.data:
                        xp_amount = int(habit_resp.data[0].get("xp_value") or 0)
                except Exception:
                    xp_amount = 0

            if xp_amount > 0:
                # Find challenge mappings for this habit
                try:
                    mappings = supabase.table("challenge_habits").select("challenge_id").eq("habit_id", habit_id).execute()
                    mappings = mappings.data if mappings.data else []
                except Exception:
                    mappings = []

                for m in mappings:
                    challenge_id = m.get("challenge_id")
                    if not challenge_id:
                        continue
                    # Ensure participant exists; if not, create participant (auto-join)
                    try:
                        part_resp = supabase.table("challenge_participants").select("id,total_points,user_name").eq("challenge_id", challenge_id).eq("user_id", user_id).execute()
                        if part_resp.data:
                            participant = part_resp.data[0]
                            current = int(participant.get("total_points") or 0)
                            new_total = current + xp_amount
                            supabase.table("challenge_participants").update({"total_points": new_total, "updated_at": datetime.utcnow().isoformat()}).eq("id", participant["id"]).execute()
                        else:
                            # Fetch user name if possible
                            try:
                                user_resp = supabase.table("users").select("display_name").eq("id", user_id).execute()
                                user_name = user_resp.data[0].get("display_name") if user_resp.data else None
                            except Exception:
                                user_name = None
                            new_part = {
                                "challenge_id": challenge_id,
                                "user_id": user_id,
                                "user_name": user_name,
                                "joined_at": datetime.utcnow().isoformat(),
                                "progress": 0,
                                "current_streak": 0,
                                "best_streak": 0,
                                "total_points": xp_amount
                            }
                            supabase.table("challenge_participants").insert(new_part).execute()
                    except Exception:
                        # ignore per-participant errors to not block habit logging
                        pass
    except Exception:
        # Fail silently: habit log should still be returned even if awarding points fails
        pass

    return result

@router.get("/logs/{habit_id}")
async def get_habit_logs(habit_id: str):
    """Get logs for a habit"""
    if not supabase:
        return []
    
    response = supabase.table("habit_logs").select("*").eq("habit_id", habit_id).order("date", desc=True).execute()
    return response.data if response.data else []