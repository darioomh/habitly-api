"""Seed script: inserts 5 initial challenges if none exist."""
from app.database import supabase
import uuid
from datetime import datetime

CHALLENGES = [
    {
        "title": "Desafío Salud Total",
        "description": "30 días de hábitos saludables: ejercicio, alimentación consciente y buen descanso. Transforma tu cuerpo y mente.",
        "category": "SALUD",
        "difficulty": "hard",
        "duration_days": 30,
        "max_participants": 1000,
        "reward": "🏆 Premium Gratis 1 Mes",
        "is_public": True,
        "start_date": "2026-05-01T00:00:00Z",
    },
    {
        "title": "Maratón de Productividad",
        "description": "30 días de máxima productividad. Despierta temprano, organiza tu día y cumple tus objetivos sin excusas.",
        "category": "PRODUCTIVIDAD",
        "difficulty": "extreme",
        "duration_days": 30,
        "max_participants": 1000,
        "reward": "💎 Badge Productividad Extrema",
        "is_public": True,
        "start_date": "2026-05-01T00:00:00Z",
    },
    {
        "title": "Reto Fitness 30",
        "description": "Ejercítate al menos 30 minutos cada día durante 30 días. Sin días de descanso, sin excusas.",
        "category": "EJERCICIO",
        "difficulty": "hard",
        "duration_days": 30,
        "max_participants": 500,
        "reward": "💪 Badge Guerrero Fitness",
        "is_public": True,
        "start_date": "2026-05-01T00:00:00Z",
    },
    {
        "title": "Desafío Mindfulness",
        "description": "Medita al menos 10 minutos cada día y registra tu reflexión. Conecta con tu interior durante 30 días.",
        "category": "MINDFULNESS",
        "difficulty": "medium",
        "duration_days": 30,
        "max_participants": 1000,
        "reward": "🧘 Badge Calma Interior",
        "is_public": True,
        "start_date": "2026-05-01T00:00:00Z",
    },
    {
        "title": "Reto Conexión Social",
        "description": "Fortalece tus vínculos. Contacta a alguien, envía un mensaje positivo o participa en comunidad cada día.",
        "category": "SOCIAL",
        "difficulty": "easy",
        "duration_days": 30,
        "max_participants": 1000,
        "reward": "🤝 Badge Conexión Social",
        "is_public": True,
        "start_date": "2026-05-01T00:00:00Z",
    },
]


def seed_challenges():
    if not supabase:
        print("⚠️ Supabase no configurado, saltando seed.")
        return

    existing = supabase.table("challenges").select("id").execute()
    if existing.data:
        print(f"✅ Ya existen {len(existing.data)} desafíos. Saltando seed.")
        return

    print("🌱 Insertando 5 desafíos iniciales...")
    for c in CHALLENGES:
        supabase.table("challenges").insert(c).execute()
        print(f"  ✅ {c['title']}")

    print("🎉 Seed completado!")


if __name__ == "__main__":
    seed_challenges()
