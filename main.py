from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api import habits, users, articles, settings, challenges, auth, squads, expeditions, seasons, flash_challenges, referrals, journal


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run seed on startup."""
    challenges.seed_challenges_on_startup()
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
