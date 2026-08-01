from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api import habits, users, articles, settings, challenges, auth, squads, expeditions, seasons, flash_challenges, referrals, journal


def check_supabase_access():
    from app.database import supabase
    if not supabase:
        print("WARNING: Supabase no configurado. Los endpoints devolverán datos demo.")
        return
    try:
        resp = supabase.table("users").select("id").limit(1).execute()
        error = getattr(resp, "error", None)
        if error:
            print(f"WARNING: No se puede leer la tabla users ({error.message}). Si SUPABASE_KEY es la anon key, el RLS bloquea el acceso. Usa la service_role key.")
        else:
            print("Supabase OK: el backend puede leer la tabla users (bypass de RLS correcto).")
    except Exception as e:
        print(f"WARNING: Error al verificar acceso a Supabase: {e}. ¿SUPABASE_KEY es la service_role key?")
        return
    try:
        col = supabase.table("users").select("password_hash").limit(1).execute()
        col_error = getattr(col, "error", None)
        if col_error and "password_hash" in str(col_error):
            print("WARNING: Falta la columna password_hash en users. Ejecuta migrations/005_password_hash.sql en el SQL Editor de Supabase.")
        else:
            print("Supabase OK: columna password_hash presente.")
    except Exception as e:
        print(f"WARNING: No se pudo verificar la columna password_hash: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run seeds and migrations on startup."""
    challenges.seed_challenges_on_startup()
    journal.migrate_journal_table()
    auth.migrate_auth_table()
    check_supabase_access()
    yield


app = FastAPI(
    title="Habitly API",
    description="API para la app de seguimiento de hábitos",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(habits.router, prefix="/api/habits", tags=["Habits"])
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(articles.router, prefix="/api/articles", tags=["Articles"])
app.include_router(settings.router, prefix="/api/settings", tags=["Settings"])
app.include_router(challenges.router, prefix="/api/challenges", tags=["Challenges"])
app.include_router(flash_challenges.router, prefix="/api/flash-challenges", tags=["Flash Challenges"])
app.include_router(referrals.router, prefix="/api/referrals", tags=["Referrals"])
app.include_router(squads.router, prefix="/api/squads", tags=["Squads"])
app.include_router(expeditions.router, prefix="/api/expeditions", tags=["Expeditions"])
app.include_router(seasons.router, prefix="/api/seasons", tags=["Seasons"])
app.include_router(journal.router, prefix="/api/journal", tags=["Journal"])


@app.get("/")
async def root():
    return {"message": "Habitly API", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
