from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta, timezone
from app.database import supabase

router = APIRouter()


def _get_current_season_dates():
    now = datetime.now(timezone.utc)
    month = now.month
    year = now.year
    start_date = datetime(year, month, 1, tzinfo=timezone.utc)
    if month == 12:
        end_date = datetime(year + 1, 1, 1, tzinfo=timezone.utc) - timedelta(seconds=1)
    else:
        end_date = datetime(year, month + 1, 1, tzinfo=timezone.utc) - timedelta(seconds=1)
    return start_date.isoformat(), end_date.isoformat()


SEASON_NAMES = [
    "Temporada de Renovación",
    "Temporada de Crecimiento",
    "Temporada de Cosecha",
    "Temporada de Reflexión",
]


@router.get("/current")
async def get_current_season():
    now = datetime.now(timezone.utc)
    season_index = (now.month - 1) // 3
    season_name = SEASON_NAMES[season_index] if season_index < len(SEASON_NAMES) else "Temporada Especial"

    start_date, end_date = _get_current_season_dates()
    quarter = (now.month - 1) // 3 + 1
    year = now.year
    label = f"Q{quarter} {year}"

    if not supabase:
        return {
            "id": f"season-{year}-q{quarter}",
            "name": season_name,
            "label": label,
            "start_date": start_date,
            "end_date": end_date,
            "is_active": True,
            "challenges_count": 4,
            "participants_count": 1280,
        }

    response = supabase.table("seasons").select("*").eq("label", label).limit(1).execute()
    if response.data:
        season = response.data[0]
        challenges_resp = supabase.table("challenges").select("id").eq("season_id", season["id"]).execute()
        season["challenges_count"] = len(challenges_resp.data) if challenges_resp.data else 0
        participants_resp = supabase.table("season_participants").select("id").eq("season_id", season["id"]).execute()
        season["participants_count"] = len(participants_resp.data) if participants_resp.data else 0
        return season

    data = {
        "name": season_name,
        "label": label,
        "start_date": start_date,
        "end_date": end_date,
        "is_active": True,
        "created_at": now.isoformat(),
    }
    created = supabase.table("seasons").insert(data).execute()
    season = created.data[0] if created.data else data
    season["challenges_count"] = 0
    season["participants_count"] = 0
    return season
