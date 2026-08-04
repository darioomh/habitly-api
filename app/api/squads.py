from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from datetime import datetime, timezone
from pydantic import BaseModel
from app.database import supabase
from app.auth import get_current_user
import uuid

router = APIRouter()


class CreateSquadRequest(BaseModel):
    name: str
    description: str
    max_members: int = 10


class JoinSquadRequest(BaseModel):
    squad_id: str
    user_name: str
    invite_code: Optional[str] = None


def _is_valid_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False


def _generate_invite_code() -> str:
    import secrets
    import string
    return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))


@router.post("")
async def create_squad(request: CreateSquadRequest, user_id: str = Depends(get_current_user)):
    if not supabase:
        return {
            "id": f"squad-{uuid.uuid4()}",
            "name": request.name,
            "description": request.description,
            "created_by": user_id,
            "invite_code": "DEMO0001",
            "max_members": request.max_members,
        }

    invite_code = _generate_invite_code()
    data = {
        "name": request.name,
        "description": request.description,
        "created_by": user_id,
        "invite_code": invite_code,
        "max_members": request.max_members,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    response = supabase.table("squads").insert(data).execute()
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to create squad")

    squad = response.data[0]

    member_data = {
        "squad_id": squad["id"],
        "user_id": user_id,
        "user_name": user_id,
        "role": "leader",
        "joined_at": datetime.now(timezone.utc).isoformat(),
    }
    supabase.table("squad_members").insert(member_data).execute()

    squad["members_count"] = 1
    return squad


@router.get("")
async def get_squads(user_id: str = Depends(get_current_user)):
    if not supabase:
        return []

    member_squad_ids = supabase.table("squad_members").select("squad_id").eq("user_id", user_id).execute()
    if not member_squad_ids.data:
        return []

    ids = [m["squad_id"] for m in member_squad_ids.data]
    response = supabase.table("squads").select("*").in_("id", ids).execute()
    squads = response.data if response.data else []

    count_resp = supabase.table("squad_members").select("squad_id").in_("squad_id", ids).execute()
    counts: dict = {}
    for row in (count_resp.data or []):
        counts[row["squad_id"]] = counts.get(row["squad_id"], 0) + 1
    for squad in squads:
        squad["members_count"] = counts.get(squad["id"], 0)

    return squads


@router.get("/{squad_id}")
async def get_squad(squad_id: str, user_id: str = Depends(get_current_user)):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase no configurado")
    if not _is_valid_uuid(squad_id):
        raise HTTPException(status_code=400, detail="Invalid squad ID format")

    response = supabase.table("squads").select("*").eq("id", squad_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Squad not found")

    membership = supabase.table("squad_members").select("id").eq("squad_id", squad_id).eq("user_id", user_id).execute()
    if not membership.data:
        raise HTTPException(status_code=403, detail="No eres miembro de este squad")

    squad = response.data[0]
    members_resp = supabase.table("squad_members").select("*").eq("squad_id", squad_id).execute()
    squad["members"] = members_resp.data if members_resp.data else []
    squad["members_count"] = len(squad["members"])
    return squad


@router.post("/join")
async def join_squad(request: JoinSquadRequest, user_id: str = Depends(get_current_user)):
    if not supabase:
        return {"id": f"member-{user_id}", "squad_id": request.squad_id, "user_id": user_id}
    if not _is_valid_uuid(request.squad_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")

    squad_resp = supabase.table("squads").select("*").eq("id", request.squad_id).execute()
    if not squad_resp.data:
        raise HTTPException(status_code=404, detail="Squad not found")
    squad = squad_resp.data[0]

    if request.invite_code and squad["invite_code"] != request.invite_code:
        raise HTTPException(status_code=403, detail="Invalid invite code")

    count_resp = supabase.table("squad_members").select("id").eq("squad_id", request.squad_id).execute()
    current_count = len(count_resp.data) if count_resp.data else 0
    if current_count >= squad["max_members"]:
        raise HTTPException(status_code=400, detail="Squad is full")

    existing = supabase.table("squad_members").select("*").eq("squad_id", request.squad_id).eq("user_id", user_id).execute()
    if existing.data:
        return existing.data[0]

    data = {
        "squad_id": request.squad_id,
        "user_id": user_id,
        "user_name": request.user_name or user_id,
        "role": "member",
        "joined_at": datetime.now(timezone.utc).isoformat(),
    }
    response = supabase.table("squad_members").insert(data).execute()
    if response.data:
        return response.data[0]
    return data


@router.post("/{squad_id}/leave")
async def leave_squad(squad_id: str, user_id: str = Depends(get_current_user)):
    if not supabase:
        return {"success": True}
    if not _is_valid_uuid(squad_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")

    supabase.table("squad_members").delete().eq("squad_id", squad_id).eq("user_id", user_id).execute()
    return {"success": True}
