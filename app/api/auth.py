from fastapi import APIRouter, HTTPException, Form, Depends
from datetime import datetime, timezone
import os
import httpx
from jose import JWTError, jwt
from app.database import supabase
from app.auth import create_access_token, create_refresh_token, verify_token, verify_refresh_token, get_current_user, hash_password, verify_password, MAX_PASSWORD_LENGTH

router = APIRouter()

GOOGLE_CERTS_URL = "https://www.googleapis.com/oauth2/v3/certs"
GOOGLE_ISSUER = "https://accounts.google.com"
# Web client ID usado por la app Android para Google Sign-In (id_token).
GOOGLE_CLIENT_ID = os.environ.get(
    "GOOGLE_CLIENT_ID",
    "604390654364-mj6srp32lvcfip7ur3jessavl0j7hbbh.apps.googleusercontent.com",
)

CREATE_AUTH_COLUMN_SQL = "ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash TEXT;"


def _run_sql(sql: str, url: str, key: str, label: str):
    try:
        r = httpx.post(
            f"{url}/sql",
            json={"query": sql},
            headers={
                "apikey": key,
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            timeout=15,
        )
        if r.status_code == 200:
            print(f"{label}: OK")
        else:
            print(f"{label} warning ({r.status_code}): {r.text[:200]}")
    except Exception as e:
        print(f"{label} error: {e}")


def migrate_auth_table():
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_KEY", "")
    if not url or not key:
        print("WARNING: Supabase not configured, skipping auth migration.")
        return
    _run_sql(CREATE_AUTH_COLUMN_SQL, url, key, "Auth table")


def _token_response(user_id: str, email: str) -> dict:
    return {
        "user_id": user_id,
        "email": email,
        "access_token": create_access_token(user_id),
        "refresh_token": create_refresh_token(user_id),
        "token_type": "bearer",
    }


def _insert_user(data: dict) -> dict:
    try:
        response = supabase.table("users").insert(data).execute()
    except Exception as e:
        message = str(e)
        if "password_hash" in message:
            raise HTTPException(
                status_code=500,
                detail="Falta la columna password_hash. Ejecuta la migración migrations/005_password_hash.sql en el SQL Editor de Supabase.",
            )
        raise HTTPException(status_code=500, detail=f"Error al crear usuario: {message}")
    if getattr(response, "error", None):
        message = str(response.error)
        if "password_hash" in message:
            raise HTTPException(
                status_code=500,
                detail="Falta la columna password_hash. Ejecuta la migración migrations/005_password_hash.sql en el SQL Editor de Supabase.",
            )
        raise HTTPException(status_code=500, detail=f"Error al crear usuario: {message}")
    if not response.data:
        raise HTTPException(
            status_code=500,
            detail="No se pudo crear el usuario. Si SUPABASE_KEY es la anon key, el RLS bloquea la escritura. Usa la service_role key.",
        )
    return response.data[0]


async def _fetch_google_jwks() -> dict:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(GOOGLE_CERTS_URL)
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"No se pudieron obtener las claves de Google: {e}")


async def verify_google_id_token(id_token: str) -> dict:
    try:
        unverified_header = jwt.get_unverified_header(id_token)
    except JWTError:
        raise HTTPException(status_code=400, detail="id_token de Google inválido")

    kid = unverified_header.get("kid")
    if not kid:
        raise HTTPException(status_code=400, detail="id_token de Google inválido (sin kid)")

    jwks = await _fetch_google_jwks()
    signing_key = next(
        (k for k in jwks.get("keys", []) if k.get("kid") == kid and k.get("kty") == "RSA"),
        None,
    )
    if signing_key is None:
        raise HTTPException(status_code=400, detail="No se pudo verificar el id_token de Google")

    try:
        return jwt.decode(
            id_token,
            signing_key,
            algorithms=["RS256"],
            audience=GOOGLE_CLIENT_ID,
            issuer=GOOGLE_ISSUER,
        )
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="id_token de Google inválido o expirado",
        )


@router.post("/login")
async def login(email: str = Form(...), password: str = Form(...)):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase no configurado")

    if not email or not password:
        raise HTTPException(status_code=400, detail="Email y contraseña son obligatorios")

    try:
        response = supabase.table("users").select("*").eq("email", email).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al consultar el usuario: {e}")
    if not response.data:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    user = response.data[0]

    password_hash = user.get("password_hash")
    if not password_hash:
        raise HTTPException(status_code=401, detail="Esta cuenta no tiene contraseña. Inicia sesión con Google.")

    if not verify_password(password, password_hash):
        raise HTTPException(status_code=401, detail="Contraseña incorrecta")

    return _token_response(user["id"], email)


@router.post("/register")
async def register(email: str = Form(...), password: str = Form(...)):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase no configurado")

    if not email or not password:
        raise HTTPException(status_code=400, detail="Email y contraseña son obligatorios")

    if len(password.encode("utf-8")) > MAX_PASSWORD_LENGTH:
        raise HTTPException(status_code=400, detail="La contraseña no puede superar los 72 caracteres")

    try:
        existing = supabase.table("users").select("*").eq("email", email).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al verificar usuario: {e}")
    if getattr(existing, "error", None):
        raise HTTPException(status_code=500, detail=f"Error al verificar usuario: {existing.error.message}")
    if existing.data:
        raise HTTPException(status_code=400, detail="El correo ya está registrado")

    data = {
        "email": email,
        "password_hash": hash_password(password),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    user = _insert_user(data)
    return _token_response(user["id"], email)


@router.post("/google")
async def google_auth(id_token: str = Form(...), email: str = Form(None)):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase no configurado")

    if not id_token:
        raise HTTPException(status_code=400, detail="id_token es obligatorio")

    payload = await verify_google_id_token(id_token)
    verified_email = payload.get("email")
    if not verified_email or not payload.get("email_verified", False):
        raise HTTPException(status_code=401, detail="La cuenta de Google no tiene un email verificado")

    try:
        existing = supabase.table("users").select("*").eq("email", verified_email).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al verificar usuario: {e}")
    if getattr(existing, "error", None):
        raise HTTPException(status_code=500, detail=f"Error al verificar usuario: {existing.error.message}")

    if existing.data:
        return _token_response(existing.data[0]["id"], verified_email)

    data = {
        "email": verified_email,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    user = _insert_user(data)
    return _token_response(user["id"], verified_email)


@router.post("/refresh")
async def refresh_token(refresh_token: str = Form(...)):
    user_id = verify_refresh_token(refresh_token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Refresh token inválido o expirado")
    return {
        "access_token": create_access_token(user_id),
        "token_type": "bearer",
    }


@router.get("/status")
async def status(user_id: str = Depends(get_current_user)):
    return {"logged_in": True, "user_id": user_id}
