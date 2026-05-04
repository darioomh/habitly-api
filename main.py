from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import habits, users, articles, settings, challenges, auth

app = FastAPI(
    title="Habitly API",
    description="API para la app de seguimiento de hábitos",
    version="1.0.0"
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

@app.get("/")
async def root():
    return {"message": "Habitly API", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
