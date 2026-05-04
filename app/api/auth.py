from fastapi import APIRouter, HTTPException, Form
from datetime import datetime
from app.database import supabase

router = APIRouter()

@router.post("/login")
async def login(email: str = Form(...), password: str = Form(...)):
    response = supabase.table("users").select("*").eq("email", email).execute()
    if not response.data:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    return {"user_id": response.data[0]["id"], "email": email}

@router.post("/register")
async def register(email: str = Form(...), password: str = Form(...)):
    existing = supabase.table("users").select("*").eq("email", email).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="El correo ya está registrado")
    
    data = {"email": email, "created_at": datetime.utcnow().isoformat()}
    response = supabase.table("users").insert(data).execute()
    return {"user_id": response.data[0]["id"], "email": email}

@router.post("/google")
async def google_auth(id_token: str = Form(...), email: str = Form(...)):
    existing = supabase.table("users").select("*").eq("email", email).execute()
    
    if existing.data:
        return {"user_id": existing.data[0]["id"], "email": email}
    
    data = {"email": email, "created_at": datetime.utcnow().isoformat()}
    response = supabase.table("users").insert(data).execute()
    return {"user_id": response.data[0]["id"], "email": email}

@router.get("/status")
async def status(user_id: str):
    return {"logged_in": True}