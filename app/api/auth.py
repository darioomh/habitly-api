from fastapi import APIRouter, HTTPException, Form, Depends
from datetime import datetime
from app.database import supabase
from app.auth import create_access_token, create_refresh_token, verify_token, get_current_user

router = APIRouter()


def _token_response(user_id: str, email: str) -> dict:
    return {
        "user_id": user_id,
        "email": email,
        "access_token": create_access_token(user_id),
        "refresh_token": create_refresh_token(user_id),
        "token_type": "bearer",
    }


@router.post("/login")
async def login(email: str = Form(...), password: str = Form(...)):
    response = supabase.table("users").select("*").eq("email", email).execute()
    if not response.data:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    user = response.data[0]
    return _token_response(user["id"], email)


@router.post("/register")
async def register(email: str = Form(...), password: str = Form(...)):
    existing = supabase.table("users").select("*").eq("email", email).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="El correo ya está registrado")

    data = {"email": email, "created_at": datetime.utcnow().isoformat()}
    response = supabase.table("users").insert(data).execute()
    user = response.data[0]
    return _token_response(user["id"], email)


@router.post("/google")
async def google_auth(id_token: str = Form(...), email: str = Form(...)):
    existing = supabase.table("users").select("*").eq("email", email).execute()

    if existing.data:
        user = existing.data[0]
        return _token_response(user["id"], email)

    data = {"email": email, "created_at": datetime.utcnow().isoformat()}
    response = supabase.table("users").insert(data).execute()
    user = response.data[0]
    return _token_response(user["id"], email)


@router.post("/refresh")
async def refresh_token(refresh_token: str = Form(...)):
    user_id = verify_token(refresh_token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Refresh token inválido o expirado")
    return {
        "access_token": create_access_token(user_id),
        "token_type": "bearer",
    }


@router.get("/status")
async def status(user_id: str = Depends(get_current_user)):
    return {"logged_in": True, "user_id": user_id}
