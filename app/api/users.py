from fastapi import APIRouter, HTTPException, Form, Body, Depends
from datetime import datetime, timedelta, date
from typing import Optional
from collections import Counter
from pydantic import BaseModel
from app.database import supabase
from app.auth import get_current_user

router = APIRouter()


def _compute_streaks(log_dates: set) -> tuple[int, int]:
    if not log_dates:
        return 0, 0

    sorted_dates = sorted(log_dates, reverse=True)
    today_d = date.today()
    yesterday_d = today_d - timedelta(days=1)

    current_streak = 0
    check = today_d
    if today_d not in log_dates and yesterday_d in log_dates:
        check = yesterday_d

    while check in log_dates:
        current_streak += 1
        check -= timedelta(days=1)

    best = 0
    run = 1
    for i in range(1, len(sorted_dates)):
        prev = sorted_dates[i - 1]
        curr = sorted_dates[i]
        if (prev - curr).days == 1:
            run += 1
        else:
            best = max(best, run)
            run = 1
    best = max(best, run)

    return current_streak, best


def _days_since_creation(user_id: str) -> int:
    try:
        resp = supabase.table("habit_logs") \
            .select("date") \
            .eq("user_id", user_id) \
            .eq("completed", True) \
            .order("date", desc=False) \
            .limit(1) \
            .execute()
        if resp.data:
            first = date.fromisoformat(resp.data[0]["date"])
            return max((date.today() - first).days, 1)
    except Exception:
        pass
    return 30


@router.get("/me")
async def get_me(user_id: str = Depends(get_current_user)):
    if not supabase:
        return {"id": user_id, "email": f"user_{user_id}@demo.com", "display_name": "Usuario Habitly"}

    response = supabase.table("users").select("*").eq("id", user_id).execute()
    if response.data:
        return response.data[0]
    return {"id": user_id, "email": f"user_{user_id}@demo.com", "display_name": "Usuario Habitly"}


@router.get("/me/stats")
async def get_me_stats(user_id: str = Depends(get_current_user)):
    if not supabase:
        return {
            "id": user_id, "display_name": "Usuario Habitly", "level": 1,
            "xp": 75, "xp_to_next_level": 100, "current_streak": 5, "best_streak": 14,
            "total_habits": 5, "completed_today": 3, "total_completed": 127,
            "completion_rate": 0.78, "streak_progress": 0.35, "habits_progress": 0.6,
            "insight": "Vas bien! Completa 2 más hábitos para superar tu media."
        }

    user_resp = supabase.table("users").select("*").eq("id", user_id).execute()
    if not user_resp.data:
        return {
            "id": user_id, "display_name": "Usuario Habitly", "level": 1,
            "xp": 0, "xp_to_next_level": 100, "current_streak": 0, "best_streak": 0,
            "total_habits": 0, "completed_today": 0, "total_completed": 0,
            "completion_rate": 0, "streak_progress": 0, "habits_progress": 0,
            "insight": "¡Crea tu primer hábito para empezar!"
        }
    user = user_resp.data[0]

    habits_resp = supabase.table("habits") \
        .select("id") \
        .eq("user_id", user_id) \
        .eq("is_active", True) \
        .execute()
    total_habits = len(habits_resp.data) if habits_resp.data else 0

    today_str = date.today().isoformat()
    logs_today = supabase.table("habit_logs") \
        .select("id") \
        .eq("user_id", user_id) \
        .eq("date", today_str) \
        .eq("completed", True) \
        .execute()
    completed_today = len(logs_today.data) if logs_today.data else 0

    all_logs_resp = supabase.table("habit_logs") \
        .select("date") \
        .eq("user_id", user_id) \
        .eq("completed", True) \
        .execute()
    all_logs = all_logs_resp.data if all_logs_resp.data else []
    total_completed = len(all_logs)
    log_dates = {date.fromisoformat(r["date"]) for r in all_logs}

    current_streak, best_streak = _compute_streaks(log_dates)

    try:
        logs_xp_resp = supabase.table("habit_logs").select("xp_earned").eq("user_id", user_id).execute()
        xp_from_logs = sum(int(r.get("xp_earned") or 0) for r in (logs_xp_resp.data or []))
    except Exception:
        xp_from_logs = total_completed * 10

    try:
        cp_resp = supabase.table("challenge_participants").select("total_points").eq("user_id", user_id).execute()
        xp_from_challenges = sum(int(r.get("total_points") or 0) for r in (cp_resp.data or []))
    except Exception:
        xp_from_challenges = 0

    try:
        sp_resp = supabase.table("season_participants").select("total_points").eq("user_id", user_id).execute()
        xp_from_seasons = sum(int(r.get("total_points") or 0) for r in (sp_resp.data or []))
    except Exception:
        xp_from_seasons = 0

    total_xp = xp_from_logs + xp_from_challenges + xp_from_seasons
    level = (total_xp // 100) + 1
    xp_in_level = total_xp % 100

    days_active = _days_since_creation(user_id)
    max_possible = total_habits * days_active
    completion_rate = round(total_completed / max_possible, 2) if max_possible > 0 else 0.0

    if total_habits == 0:
        insight = "¡Crea tu primer hábito para empezar!"
    elif completed_today == total_habits:
        insight = "¡Todos los hábitos completados hoy! Sigue así."
    elif current_streak >= 7:
        insight = f"🔥 Llevas {current_streak} días seguidos. ¡Imparable!"
    else:
        remaining = total_habits - completed_today
        insight = f"Hoy has completado {completed_today} de {total_habits} hábitos. Te quedan {remaining}."

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
        "completion_rate": min(completion_rate, 1.0),
        "streak_progress": min(current_streak / 30, 1.0),
        "habits_progress": completed_today / total_habits if total_habits > 0 else 0,
        "insight": insight,
        "total_xp": total_xp,
    }


@router.get("/me/achievements")
async def get_me_achievements(user_id: str = Depends(get_current_user)):
    if not supabase:
        return [
            {"label": "Primer hábito", "unlocked": True, "unlocked_at": None},
            {"label": "Racha 7d", "unlocked": False, "unlocked_at": None},
        ]

    resp = supabase.table("user_achievements").select("label, unlocked, unlocked_at").eq("user_id", user_id).execute()
    if resp.data:
        return resp.data
    return []


@router.post("/me/achievements")
async def report_me_achievement(achievement: dict = Body(...), user_id: str = Depends(get_current_user)):
    if not supabase:
        return {"success": True}

    label = achievement.get("label")
    unlocked = achievement.get("unlocked", False)
    unlocked_at = achievement.get("unlocked_at") or datetime.utcnow().isoformat() if unlocked else None

    existing = supabase.table("user_achievements").select("id, unlocked").eq("user_id", user_id).eq("label", label).execute()
    if existing.data:
        data = {"unlocked": unlocked, "updated_at": datetime.utcnow().isoformat()}
        if unlocked and unlocked_at:
            data["unlocked_at"] = unlocked_at
        supabase.table("user_achievements").update(data).eq("id", existing.data[0]["id"]).execute()
        return {"success": True}
    else:
        data = {
            "user_id": user_id,
            "label": label,
            "unlocked": unlocked,
            "unlocked_at": unlocked_at,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        supabase.table("user_achievements").insert(data).execute()
        return {"success": True}


@router.get("/me/weekly-activity")
async def get_me_weekly_activity(user_id: str = Depends(get_current_user)):
    if not supabase:
        demo = []
        for i in range(7):
            d = (date.today() - timedelta(days=6 - i)).isoformat()
            demo.append({"date": d, "count": 3 if i < 5 else 1})
        return demo

    seven_days_ago = (date.today() - timedelta(days=6)).isoformat()
    logs_resp = supabase.table("habit_logs") \
        .select("date") \
        .eq("user_id", user_id) \
        .eq("completed", True) \
        .gte("date", seven_days_ago) \
        .execute()

    counts = Counter(r["date"] for r in logs_resp.data) if logs_resp.data else Counter()

    result = []
    for i in range(7):
        d = (date.today() - timedelta(days=6 - i)).isoformat()
        result.append({"date": d, "count": counts.get(d, 0)})
    return result

@router.post("")
async def create_user(user_id: str = Form(...), email: str = Form(...), display_name: Optional[str] = Form(None)):
    if not supabase:
        return {"id": user_id, "email": email}

    existing = supabase.table("users").select("*").eq("id", user_id).execute()
    if existing.data:
        return existing.data[0]

    data = {"id": user_id, "email": email, "display_name": display_name, "created_at": datetime.utcnow().isoformat()}
    response = supabase.table("users").insert(data).execute()
    return response.data[0] if response.data else data

@router.get("/me/preferences")
async def get_me_preferences(user_id: str = Depends(get_current_user)):
    if not supabase:
        return {"theme": "system", "notifications": True}

    response = supabase.table("user_preferences").select("*").eq("user_id", user_id).execute()
    if response.data:
        return response.data[0]
    return {"theme": "system", "notifications": True, "reminder_time": "09:00"}

@router.put("/me/preferences")
async def update_me_preferences(
    theme: Optional[str] = None,
    notifications: Optional[bool] = None,
    reminder_time: Optional[str] = None,
    user_id: str = Depends(get_current_user)
):
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


class FcmTokenRequest(BaseModel):
    fcm_token: str
    device_info: Optional[str] = None


@router.post("/fcm-token")
async def register_fcm_token(request: FcmTokenRequest, user_id: str = Depends(get_current_user)):
    if not supabase:
        return {"success": True}

    existing = supabase.table("user_fcm_tokens").select("id").eq("user_id", user_id).eq("fcm_token", request.fcm_token).execute()
    if existing.data:
        supabase.table("user_fcm_tokens").update({"updated_at": datetime.utcnow().isoformat()}).eq("id", existing.data[0]["id"]).execute()
        return {"success": True}

    data = {
        "user_id": user_id,
        "fcm_token": request.fcm_token,
        "device_info": request.device_info,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }
    supabase.table("user_fcm_tokens").insert(data).execute()
    return {"success": True}


@router.delete("/me")
async def delete_me(user_id: str = Depends(get_current_user)):
    if not supabase:
        return {"success": True}

    tables_to_clean = [
        "habit_logs", "habits", "habit_reminders",
        "user_achievements", "user_preferences", "user_fcm_tokens",
        "journal_entries", "challenge_participants",
        "season_participants", "referral_progress",
    ]
    for table in tables_to_clean:
        try:
            supabase.table(table).delete().eq("user_id", user_id).execute()
        except Exception:
            pass

    supabase.table("users").delete().eq("id", user_id).execute()
    return {"success": True}
