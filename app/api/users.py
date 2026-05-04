from fastapi import APIRouter, HTTPException, Form
from datetime import datetime
from typing import Optional
from app.database import supabase

router = APIRouter()

@router.get("/{user_id}")
async def get_user(user_id: str):
    """Get user by ID"""
    if not supabase:
        return {"id": user_id, "email": f"user_{user_id}@demo.com", "display_name": "Usuario Habitly"}
    
    response = supabase.table("users").select("*").eq("id", user_id).execute()
    if response.data:
        return response.data[0]
    return {"id": user_id, "email": f"user_{user_id}@demo.com", "display_name": "Usuario Habitly"}

@router.get("/{user_id}/stats")
async def get_user_stats(user_id: str):
    """Get user statistics"""
    if not supabase:
        return {
            "id": user_id,
            "display_name": "Usuario Habitly",
            "level": 1,
            "xp": 75,
            "xp_to_next_level": 100,
            "current_streak": 5,
            "best_streak": 14,
            "total_habits": 5,
            "completed_today": 3,
            "total_completed": 127,
            "completion_rate": 0.78,
            "streak_progress": 0.35,
            "habits_progress": 0.6,
            "insight": "Vas bien! Completa 2 más hábitos para superar tu media."
        }
    
    # Get user
    user_response = supabase.table("users").select("*").eq("id", user_id).execute()
    if not user_response.data:
        return {
            "id": user_id,
            "display_name": "Usuario Habitly",
            "level": 1,
            "xp": 0,
            "xp_to_next_level": 100,
            "current_streak": 0,
            "best_streak": 0,
            "total_habits": 0,
            "completed_today": 0,
            "total_completed": 0,
            "completion_rate": 0,
            "streak_progress": 0,
            "habits_progress": 0,
            "insight": "¡Crea tu primer hábito para empezar!"
        }
    
    user = user_response.data[0]
    
    # Get habits count
    habits_response = supabase.table("habits").select("id", count="exact").eq("user_id", user_id).eq("is_active", True).execute()
    total_habits = len(habits_response.data) if habits_response.data else 0
    
    # Get completed today
    today = datetime.utcnow().date().isoformat()
    logs_today = supabase.table("habit_logs").select("id").eq("user_id", user_id).eq("date", today).eq("completed", True).execute()
    completed_today = len(logs_today.data) if logs_today.data else 0
    
    # Get total completed
    all_logs = supabase.table("habit_logs").select("id").eq("user_id", user_id).eq("completed", True).execute()
    total_completed = len(all_logs.data) if all_logs.data else 0
    
    # Calculate completion rate
    completion_rate = (total_completed / (total_habits * 30) * 100) / 100 if total_habits > 0 else 0
    
    # Calculate XP and level
    xp = total_completed * 10
    level = (xp // 100) + 1
    xp_in_level = xp % 100
    
    # Calculate streak (simplified)
    current_streak = min(completed_today, 7) if completed_today > 0 else 0
    best_streak = max(current_streak, 14)
    
    return {
        "id": user_id,
        "display_name": user.get("display_name", "Usuario Habitly"),
        "email": user.get("email", ""),
        "level": level,
        "xp": xp_in_level,
        "xp_to_next_level": 100,
        "current_streak": current_streak,
        "best_streak": best_streak,
        "total_habits": total_habits,
        "completed_today": completed_today,
        "total_completed": total_completed,
        "completion_rate": completion_rate,
        "streak_progress": current_streak / 30,
        "habits_progress": completed_today / total_habits if total_habits > 0 else 0,
        "insight": f"Hoy has completado {completed_today} de {total_habits} hábitos."
    }

@router.post("")
async def create_user(user_id: str = Form(...), email: str = Form(...), display_name: Optional[str] = Form(None)):
    """Create user"""
    if not supabase:
        return {"id": user_id, "email": email}
    
    # Check if user already exists
    existing = supabase.table("users").select("*").eq("id", user_id).execute()
    if existing.data:
        return existing.data[0]
    
    data = {"id": user_id, "email": email, "display_name": display_name, "created_at": datetime.utcnow().isoformat()}
    response = supabase.table("users").insert(data).execute()
    return response.data[0] if response.data else data

@router.get("/{user_id}/preferences")
async def get_preferences(user_id: str):
    """Get user preferences"""
    if not supabase:
        return {"theme": "system", "notifications": True}
    
    response = supabase.table("user_preferences").select("*").eq("user_id", user_id).execute()
    if response.data:
        return response.data[0]
    return {"theme": "system", "notifications": True, "reminder_time": "09:00"}

@router.put("/{user_id}/preferences")
async def update_preferences(
    user_id: str,
    theme: Optional[str] = None,
    notifications: Optional[bool] = None,
    reminder_time: Optional[str] = None
):
    """Update user preferences"""
    if not supabase:
        return {"success": True}
    
    data = {"updated_at": datetime.utcnow().isoformat()}
    if theme: data["theme"] = theme
    if notifications is not None: data["notifications"] = notifications
    if reminder_time: data["reminder_time"] = reminder_time
    
    existing = supabase.table("user_preferences").select("id").eq("user_id", user_id).execute()
    
    if existing.data:
        response = supabase.table("user_preferences").update(data).eq("user_id", user_id).execute()
    else:
        data["user_id"] = user_id
        data["created_at"] = datetime.utcnow().isoformat()
        response = supabase.table("user_preferences").insert(data).execute()
    
    return response.data[0] if response.data else {"success": True}