from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timedelta, timezone
from typing import Optional
from pydantic import BaseModel
from app.database import supabase
from app.auth import get_current_user
import uuid
import random

router = APIRouter()


class UpdateProgressRequest(BaseModel):
    stage_index: int
    completed: bool = True


DEFAULT_STAGES = [
    {"title": "El Despertar", "description": "Completa tu primer hábito del día", "required_habits": 1, "reward": "?? 50 XP"},
    {"title": "Ritmo Constante", "description": "Mantén una racha de 3 días", "required_streak": 3, "reward": "?? 100 XP"},
    {"title": "Explorador", "description": "Prueba una nueva categoría de hábito", "required_habits": 1, "reward": "?? Badge Explorador"},
    {"title": "Disciplina de Acero", "description": "Completa 7 días seguidos", "required_streak": 7, "reward": "?? 200 XP"},
    {"title": "Maestro del Tiempo", "description": "Completa hábitos en 5 días distintos", "required_days": 5, "reward": "?? 150 XP"},
    {"title": "Conexión Social", "description": "Invita a un amigo a la app", "required_invites": 1, "reward": "?? Badge Social"},
    {"title": "Resistencia", "description": "Alcanza 14 días de racha", "required_streak": 14, "reward": "?? 300 XP"},
    {"title": "Versatilidad", "description": "Completa hábitos de 3 categorías distintas", "required_categories": 3, "reward": "?? 250 XP"},
    {"title": "Leyenda Viviente", "description": "Llega a 30 días de racha", "required_streak": 30, "reward": "?? Badge Leyenda"},
    {"title": "Expedición Completa", "description": "Completa todas las etapas anteriores", "required_all_previous": True, "reward": "?? Corona de la Expedición"},
]


def _initialize_expedition(user_id: str) -> dict:
    stages = [
        {**stage, "completed": False, "completed_at": None}
        for stage in DEFAULT_STAGES
    ]
    data = {
        "user_id": user_id,
        "stages": stages,
        "current_stage": 0,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "completed": False,
    }
    response = supabase.table("expeditions").insert(data).execute()
    return response.data[0] if response.data else data


@router.get("/active")
async def get_active_expedition(user_id: str = Depends(get_current_user)):
    if not supabase:
        stages = [
            {**stage, "completed": i < 2, "completed_at": datetime.now(timezone.utc).isoformat() if i < 2 else None}
            for i, stage in enumerate(DEFAULT_STAGES)
        ]
        return {
            "id": f"expedition-{user_id}",
            "user_id": user_id,
            "stages": stages,
            "current_stage": 2,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "completed": False,
        }

    try:
        uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    response = supabase.table("expeditions").select("*").eq("user_id", user_id).order("started_at", desc=True).limit(1).execute()
    if response.data:
        expedition = response.data[0]
        if not expedition.get("completed"):
            return expedition

    return _initialize_expedition(user_id)


@router.get("/{expedition_id}")
async def get_expedition(expedition_id: str, user_id: str = Depends(get_current_user)):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase no configurado")
    try:
        uuid.UUID(expedition_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid expedition ID format")

    response = supabase.table("expeditions").select("*").eq("id", expedition_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Expedition not found")
    expedition = response.data[0]
    if str(expedition.get("user_id")) != str(user_id):
        raise HTTPException(status_code=403, detail="No tienes acceso a esta expedición")
    return expedition


@router.post("/{expedition_id}/progress")
async def update_expedition_progress(expedition_id: str, request: UpdateProgressRequest, user_id: str = Depends(get_current_user)):
    if not supabase:
        return {"success": True}

    try:
        uuid.UUID(expedition_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid expedition ID format")

    response = supabase.table("expeditions").select("*").eq("id", expedition_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Expedition not found")

    expedition = response.data[0]
    if str(expedition.get("user_id")) != str(user_id):
        raise HTTPException(status_code=403, detail="No tienes acceso a esta expedición")
    stages = expedition.get("stages", [])

    if request.stage_index < 0 or request.stage_index >= len(stages):
        raise HTTPException(status_code=400, detail="Invalid stage index")

    if stages[request.stage_index]["completed"]:
        return expedition

    stages[request.stage_index]["completed"] = True
    stages[request.stage_index]["completed_at"] = datetime.now(timezone.utc).isoformat()

    next_stage = request.stage_index + 1
    all_completed = next_stage >= len(stages)

    update_data = {
        "stages": stages,
        "current_stage": next_stage if not all_completed else len(stages),
        "completed": all_completed,
    }

    supabase.table("expeditions").update(update_data).eq("id", expedition_id).execute()
    expedition.update(update_data)
    return expedition
