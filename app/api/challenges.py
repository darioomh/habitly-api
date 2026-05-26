from fastapi import APIRouter, HTTPException, Query, Body
from datetime import datetime, timedelta, date
import calendar
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

@router.put("/{challenge_id}/progress")
async def update_progress_put(challenge_id: str, request: UpdateProgressRequest):
    return await update_progress(challenge_id, request)

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

@router.get("/{challenge_id}/leaderboard")
async def get_leaderboard(challenge_id: str):
    if not supabase:
        return []
    if not is_valid_uuid(challenge_id):
        raise HTTPException(status_code=400, detail="Invalid challenge ID format")
    try:
        response = (
            supabase.table("challenge_participants")
            .select("*")
            .eq("challenge_id", challenge_id)
            .order("total_points", desc=True)
            .execute()
        )
        return response.data if response.data else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post("/auto-link-habits")
async def auto_link_habits(category: Optional[str] = None):
    """Auto-link habits to challenges by matching category (case-insensitive).
    If category is provided, only process that category.
    """
    if not supabase:
        return {"linked": 0, "details": [], "note": "Supabase not configured"}
    try:
        # fetch active challenges
        ch_resp = supabase.table("challenges").select("id,category,title,is_active").execute()
        challenges = ch_resp.data if ch_resp.data else []
        # fetch habits
        habits_resp = supabase.table("habits").select("id,category").execute()
        habits = habits_resp.data if habits_resp.data else []

        linked = 0
        details = []
        for ch in challenges:
            if not ch.get("is_active"):
                continue
            ch_cat = (ch.get("category") or "").strip().upper()
            if category and ch_cat != (category.strip().upper()):
                continue
            for h in habits:
                h_cat = (h.get("category") or "").strip().upper()
                if not h_cat or h_cat != ch_cat:
                    continue
                # check existing mapping
                exists = supabase.table("challenge_habits").select("id").eq("challenge_id", ch["id"]).eq("habit_id", h["id"]).execute()
                if exists.data:
                    continue
                # insert mapping
                supabase.table("challenge_habits").insert({"challenge_id": ch["id"], "habit_id": h["id"], "created_at": datetime.utcnow().isoformat()}).execute()
                linked += 1
                details.append({"challenge_id": ch["id"], "habit_id": h["id"], "challenge_title": ch.get("title")})

        return {"linked": linked, "details": details}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post("/reset-monthly")
async def reset_monthly_challenges(year: Optional[int] = None, month: Optional[int] = None, create_premium: bool = True):
    """Delete existing challenges and create one monthly challenge per category. Also create an optional premium challenge for the month."""
    if not supabase:
        return {"created": 0, "note": "Supabase not configured"}
    try:
        today = datetime.utcnow().date()
        if not year:
            year = today.year
        if not month:
            month = today.month
        # compute start and end of month
        start_date = datetime(year, month, 1).isoformat()
        last_day = calendar.monthrange(year, month)[1]
        end_date = datetime(year, month, last_day, 23, 59, 59).isoformat()

        # Delete existing challenges and mappings
        try:
            supabase.table("challenge_habits").delete().execute()
        except Exception:
            pass
        try:
            supabase.table("challenge_participants").delete().execute()
        except Exception:
            pass
        try:
            supabase.table("challenges").delete().execute()
        except Exception:
            pass

        # Discover categories from habits
        cats_resp = supabase.table("habits").select("category").execute()
        cats = [ (r.get("category") or "").strip().upper() for r in (cats_resp.data or []) ]
        cats = sorted(set([c for c in cats if c]))
        if not cats:
            # fallback categories
            cats = ["SALUD", "PRODUCTIVIDAD", "EJERCICIO", "MINDFULNESS", "SOCIAL"]

        created = 0
        created_details = []
        for cat in cats:
            title = f"{cat} - {month:02d}/{year}"
            challenge = {
                "title": title,
                "description": f"Desafío mensual de {cat} para {month:02d}/{year}",
                "category": cat,
                "difficulty": "medium",
                "duration_days": last_day,
                "max_participants": 10000,
                "reward": "Badge",
                "is_premium_required": False,
                "is_public": True,
                "is_live": True,
                "is_active": True,
                "start_date": start_date,
                "end_date": end_date,
                "created_at": datetime.utcnow().isoformat()
            }
            resp = supabase.table("challenges").insert(challenge).execute()
            if resp.data:
                ch = resp.data[0]
                created += 1
                created_details.append(ch)
                # auto-link habits of same category
                try:
                    habits_resp = supabase.table("habits").select("id").eq("category", cat).execute()
                    habits = habits_resp.data if habits_resp.data else []
                    for h in habits:
                        supabase.table("challenge_habits").insert({"challenge_id": ch.get("id"), "habit_id": h.get("id"), "created_at": datetime.utcnow().isoformat()}).execute()
                except Exception:
                    pass

        if create_premium:
            title = f"PREMIUM - {month:02d}/{year}"
            premium = {
                "title": title,
                "description": "Desafío exclusivo para suscriptores Premium",
                "category": "PREMIUM",
                "difficulty": "hard",
                "duration_days": last_day,
                "max_participants": 10000,
                "reward": "Premium Badge",
                "is_premium_required": True,
                "is_public": True,
                "is_live": True,
                "is_active": True,
                "start_date": start_date,
                "end_date": end_date,
                "created_at": datetime.utcnow().isoformat()
            }
            p_resp = supabase.table("challenges").insert(premium).execute()
            if p_resp.data:
                created_details.append(p_resp.data[0])
                created += 1

        return {"created": created, "details": created_details}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post("/{challenge_id}/invites")
async def track_challenge_invite(challenge_id: str, payload: Dict[str, Any] = Body(...)):
    if not supabase:
        return {"challenge_id": challenge_id, "user_id": payload.get("user_id", ""), "invite_count": 1}
    user_id = payload.get("user_id")
    if not user_id or not is_valid_uuid(challenge_id) or not is_valid_uuid(user_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")
    try:
        existing = (
            supabase.table("challenge_invites")
            .select("*")
            .eq("challenge_id", challenge_id)
            .eq("user_id", user_id)
            .execute()
        )
        if existing.data:
            current = existing.data[0]
            invite_count = int(current.get("invite_count") or 0) + 1
            response = (
                supabase.table("challenge_invites")
                .update({"invite_count": invite_count, "updated_at": datetime.utcnow().isoformat()})
                .eq("id", current["id"])
                .execute()
            )
            return response.data[0] if response.data else {**current, "invite_count": invite_count}
        data = {
            "challenge_id": challenge_id,
            "user_id": user_id,
            "invite_count": 1,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        response = supabase.table("challenge_invites").insert(data).execute()
        return response.data[0] if response.data else data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/points-log/list")
async def get_challenge_points_log(
    challenge_id: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200)
):
    """Get paginated challenge points log. Filters by challenge_id and/or user_id."""
    if not supabase:
        return {"items": [], "total": 0, "page": page, "per_page": per_page}
    try:
        resp = supabase.table("challenge_points_log").select("*").order("created_at", desc=True).execute()
        items = resp.data if resp.data else []
        if challenge_id:
            items = [i for i in items if i.get("challenge_id") == challenge_id]
        if user_id:
            items = [i for i in items if i.get("user_id") == user_id]
        total = len(items)
        start = (page - 1) * per_page
        end = start + per_page
        return {"items": items[start:end], "total": total, "page": page, "per_page": per_page}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post("/{challenge_id}/participants/{user_id}/add-points")
async def add_points_to_participant(challenge_id: str, user_id: str, payload: Dict[str, int] = Body(...)):
    """Add points to a challenge participant (increments total_points).
    Body: { "points": 10 }
    """
    if not supabase:
        # Demo response when DB not configured
        points = int(payload.get("points") or 0)
        return {"challenge_id": challenge_id, "user_id": user_id, "added": points, "total_points": points}

    if not is_valid_uuid(challenge_id) or not is_valid_uuid(user_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")

    try:
        points = int(payload.get("points") or 0)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid points value")

    if points <= 0:
        raise HTTPException(status_code=400, detail="Points must be a positive integer")

    try:
        resp = supabase.table("challenge_participants").select("id,total_points").eq("challenge_id", challenge_id).eq("user_id", user_id).execute()
        if not resp.data:
            raise HTTPException(status_code=404, detail="Participant not found")

        participant = resp.data[0]
        current = int(participant.get("total_points") or 0)
        new_total = current + points

        update_resp = supabase.table("challenge_participants").update({"total_points": new_total, "updated_at": datetime.utcnow().isoformat()}).eq("id", participant["id"]).execute()
        if update_resp.data:
            return update_resp.data[0]
        # Fallback
        return {"challenge_id": challenge_id, "user_id": user_id, "total_points": new_total}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
