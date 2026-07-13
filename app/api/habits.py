from fastapi import APIRouter, HTTPException, Query, Body, BackgroundTasks, Depends
from typing import List, Optional, Dict, Any
from datetime import datetime
import os
import httpx
import asyncio
from app.database import supabase
from app.models.models import Habit, HabitCreate
from app.auth import get_current_user

router = APIRouter()


async def send_fcm_notification_async(tokens: List[str], title: str, body: str, data: Dict[str, Any] | None = None) -> bool:
    key = os.getenv("FCM_SERVER_KEY")
    if not key or not tokens:
        return False
    headers = {"Authorization": f"key={key}", "Content-Type": "application/json"}
    payload = {"registration_ids": tokens, "notification": {"title": title, "body": body}, "data": data or {}}
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post("https://fcm.googleapis.com/fcm/send", json=payload, headers=headers, timeout=5.0)
            return resp.status_code == 200
    except Exception:
        return False

@router.get("")
async def get_habits(
    user_id: str = Depends(get_current_user),
    is_active: Optional[bool] = True
):
    if not supabase:
        return []

    query = supabase.table("habits").select("*").eq("user_id", user_id)
    if is_active is not None:
        query = query.eq("is_active", is_active)

    response = query.order("created_at", desc=True).execute()
    return response.data if response.data else []

@router.get("/{habit_id}")
async def get_habit(habit_id: str):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase no configurado")

    response = supabase.table("habits").select("*").eq("id", habit_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Habit not found")
    return response.data[0]

@router.post("")
async def create_habit(habit: HabitCreate, user_id: str = Depends(get_current_user)):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase no configurado")

    data = habit.model_dump()
    data["user_id"] = user_id
    data["created_at"] = datetime.utcnow().isoformat()
    data["updated_at"] = datetime.utcnow().isoformat()

    response = supabase.table("habits").insert(data).execute()
    if response.error:
        raise HTTPException(status_code=500, detail=response.error.message)
    return response.data[0]

@router.put("/{habit_id}")
async def update_habit(habit_id: str, title: Optional[str] = None, description: Optional[str] = None):
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
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase no configurado")

    response = supabase.table("habits").update({"is_active": False}).eq("id", habit_id).execute()
    if response.error:
        raise HTTPException(status_code=500, detail=response.error.message)
    return {"success": True}

@router.post("/logs")
async def create_habit_log(
    habit_id: str,
    date: str,
    completed: bool = False,
    notes: Optional[str] = None,
    background_tasks: BackgroundTasks = None,
    user_id: str = Depends(get_current_user)
):
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

    existing = supabase.table("habit_logs").select("*").eq("habit_id", habit_id).eq("date", date).execute()

    if existing.data:
        response = supabase.table("habit_logs").update(data).eq("id", existing.data[0]["id"]).execute()
    else:
        response = None

    if existing.data:
        response = supabase.table("habit_logs").update(data).eq("id", existing.data[0]["id"]).execute()
    else:
        response = supabase.table("habit_logs").insert(data).execute()

    result = response.data[0] if response.data else data

    prev_completed = False
    was_new = False
    if existing.data:
        prev_completed = bool(existing.data[0].get("completed"))
    else:
        was_new = True

    try:
        if completed and (was_new or (existing.data and not prev_completed)):
            xp_amount = int(result.get("xp_earned") or 0)
            if xp_amount == 0:
                try:
                    habit_resp = supabase.table("habits").select("xp_value").eq("id", habit_id).execute()
                    if habit_resp.data:
                        xp_amount = int(habit_resp.data[0].get("xp_value") or 0)
                except Exception:
                    xp_amount = 0

            if xp_amount > 0:
                try:
                    mappings = supabase.table("challenge_habits").select("challenge_id").eq("habit_id", habit_id).execute()
                    mappings = mappings.data if mappings.data else []
                except Exception:
                    mappings = []

                for m in mappings:
                    challenge_id = m.get("challenge_id")
                    if not challenge_id:
                        continue

                    habit_log_id = result.get("id")
                    try:
                        if habit_log_id:
                            existing_log_check = supabase.table("challenge_points_log").select("id").eq("reason", f"habit_log:{habit_log_id}").execute()
                            if existing_log_check.data:
                                continue
                    except Exception:
                        pass

                    try:
                        part_resp = supabase.table("challenge_participants").select("id,total_points,user_name").eq("challenge_id", challenge_id).eq("user_id", user_id).execute()
                        participant_id = None
                        if part_resp.data:
                            participant = part_resp.data[0]
                            current = int(participant.get("total_points") or 0)
                            new_total = current + xp_amount
                            supabase.table("challenge_participants").update({"total_points": new_total, "updated_at": datetime.utcnow().isoformat()}).eq("id", participant["id"]).execute()
                            participant_id = participant.get("id")
                        else:
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
                            insert_resp = supabase.table("challenge_participants").insert(new_part).execute()
                            if insert_resp.data:
                                participant_id = insert_resp.data[0].get("id")
                            new_total = xp_amount

                        try:
                            log_entry = {
                                "challenge_id": challenge_id,
                                "user_id": user_id,
                                "habit_id": habit_id,
                                "points": xp_amount,
                                "reason": f"habit_log:{habit_log_id or ''}",
                                "created_at": datetime.utcnow().isoformat()
                            }
                            supabase.table("challenge_points_log").insert(log_entry).execute()
                        except Exception:
                            pass

                        try:
                            ch_title = "Desafío"
                            try:
                                ch_resp = supabase.table("challenges").select("title").eq("id", challenge_id).execute()
                                if ch_resp.data:
                                    ch_title = ch_resp.data[0].get("title") or ch_title
                            except Exception:
                                pass

                            tokens_resp = supabase.table("user_fcm_tokens").select("fcm_token").eq("user_id", user_id).execute()
                            tokens = [r.get("fcm_token") for r in (tokens_resp.data or [])]

                            if tokens:
                                title = f"Ganaste {xp_amount} XP"
                                body = f"Has recibido {xp_amount} XP por completar un hábito en {ch_title}."
                                try:
                                    if background_tasks:
                                        background_tasks.add_task(send_fcm_notification_async, tokens, title, body, {"challenge_id": challenge_id, "points": xp_amount})
                                    else:
                                        try:
                                            asyncio.create_task(send_fcm_notification_async(tokens, title, body, {"challenge_id": challenge_id, "points": xp_amount}))
                                        except Exception:
                                            try:
                                                httpx.post("https://fcm.googleapis.com/fcm/send", json={"registration_ids": tokens, "notification": {"title": title, "body": body}, "data": {"challenge_id": challenge_id, "points": xp_amount}}, headers={"Authorization": f"key={os.getenv('FCM_SERVER_KEY')}", "Content-Type": "application/json"}, timeout=5.0)
                                            except Exception:
                                                pass
                                except Exception:
                                    pass
                        except Exception:
                            pass

                    except Exception:
                        pass
    except Exception:
        pass

    return result

@router.get("/logs/{habit_id}")
async def get_habit_logs(habit_id: str):
    if not supabase:
        return []

    response = supabase.table("habit_logs").select("*").eq("habit_id", habit_id).order("date", desc=True).execute()
    return response.data if response.data else []
