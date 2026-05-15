from datetime import datetime, timedelta
from typing import List, Optional

import httpx
from fastapi import APIRouter, HTTPException, Query

from app.database import supabase

router = APIRouter()

ARTICLE_IMAGES = {
    "wellness": "https://images.unsplash.com/photo-1506126613408-eca07ce68773?auto=format&fit=crop&w=1400&q=85",
    "productivity": "https://images.unsplash.com/photo-1497366754035-f200968a6e72?auto=format&fit=crop&w=1400&q=85",
    "health": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=1400&q=85",
    "finance": "https://images.unsplash.com/photo-1554224155-6726b3ff858f?auto=format&fit=crop&w=1400&q=85",
}

ARTICLES = [
    {
        "id": "1",
        "title": "Cómo crear un hábito en 30 días",
        "excerpt": "La ciencia detrás de la formación de hábitos.",
        "source": "Habitly Journal",
        "source_url": "https://habitly.app/blog",
        "author": "Equipo Habitly",
        "category": "wellness",
        "image_url": "https://images.unsplash.com/photo-1499209974431-9dddcece7f88?auto=format&fit=crop&w=1400&q=85",
    },
    {
        "id": "2",
        "title": "El poder del seguimiento visual",
        "excerpt": "Por qué ver tu progreso aumenta la motivación.",
        "source": "Productivity Weekly",
        "source_url": "https://productivityweekly.com",
        "author": "Sarah Chen",
        "category": "productivity",
        "image_url": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=1400&q=85",
    },
    {
        "id": "3",
        "title": "Meditación para principiantes",
        "excerpt": "Una guía simple de 5 minutos para meditar.",
        "source": "Mindful Living",
        "source_url": "https://mindfulliving.com",
        "author": "Miguel Santos",
        "category": "wellness",
        "image_url": "https://images.unsplash.com/photo-1508672019048-805c876b67e2?auto=format&fit=crop&w=1400&q=85",
    },
    {
        "id": "4",
        "title": "Regla de los 2 minutos",
        "excerpt": "La técnica más simple contra la procrastinación.",
        "source": "Habit Design",
        "source_url": "https://jamesclear.com/how-to-stop-procrastinating",
        "author": "James Clear",
        "category": "productivity",
        "image_url": "https://images.unsplash.com/photo-1484480974693-6ca0a78fb36b?auto=format&fit=crop&w=1400&q=85",
    },
    {
        "id": "5",
        "title": "Sueño y aprendizaje",
        "excerpt": "Cómo el sueño afecta tu capacidad de aprender.",
        "source": "Neuroscience Daily",
        "source_url": "https://neurosciencedaily.com",
        "author": "Dr. Anna Berg",
        "category": "health",
        "image_url": "https://images.unsplash.com/photo-1455642305367-68834a9d7d44?auto=format&fit=crop&w=1400&q=85",
    },
    {
        "id": "6",
        "title": "El método Pomodoro",
        "excerpt": "Trabaja en sprints de 25 minutos.",
        "source": "Lifehacker",
        "source_url": "https://lifehacker.com",
        "author": "Laura Mark",
        "category": "productivity",
        "image_url": "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1400&q=85",
    },
    {
        "id": "7",
        "title": "Gratitud diaria",
        "excerpt": "Por qué escribir 3 cosas por agradecer.",
        "source": "Psychology Today",
        "source_url": "https://psychologytoday.com",
        "author": "Dr. Robert Emmons",
        "category": "wellness",
        "image_url": "https://images.unsplash.com/photo-1517842645767-c639042777db?auto=format&fit=crop&w=1400&q=85",
    },
    {
        "id": "8",
        "title": "Finanzas personales básicas",
        "excerpt": "5 hábitos para construir riqueza.",
        "source": "Finance Field Notes",
        "source_url": "https://financeguru.com",
        "author": "Mark Cuban",
        "category": "finance",
        "image_url": "https://images.unsplash.com/photo-1554224154-26032ffc0d07?auto=format&fit=crop&w=1400&q=85",
    },
    {
        "id": "9",
        "title": "Ejercicio matutino",
        "excerpt": "Los beneficios de hacer ejercicio por la mañana.",
        "source": "Health Magazine",
        "source_url": "https://healthmagazine.com",
        "author": "Dr. Fitness",
        "category": "health",
        "image_url": "https://images.unsplash.com/photo-1518611012118-696072aa579a?auto=format&fit=crop&w=1400&q=85",
    },
    {
        "id": "10",
        "title": "Mindfulness en el trabajo",
        "excerpt": "Técnicas de mindfulness para aplicar en la oficina.",
        "source": "WorkLife",
        "source_url": "https://worklife.com",
        "author": "Ana García",
        "category": "wellness",
        "image_url": "https://images.unsplash.com/photo-1497366811353-6870744d04b2?auto=format&fit=crop&w=1400&q=85",
    },
    {
        "id": "11",
        "title": "Alimentación inteligente",
        "excerpt": "Comer bien sin complicarte la vida.",
        "source": "Nutrition Pro",
        "source_url": "https://nutritionpro.com",
        "author": "Carlos Ruiz",
        "category": "health",
        "image_url": "https://images.unsplash.com/photo-1498837167922-ddd27525d352?auto=format&fit=crop&w=1400&q=85",
    },
    {
        "id": "12",
        "title": "Gestión del tiempo",
        "excerpt": "Aprende a dominar tu agenda.",
        "source": "Time Masters",
        "source_url": "https://timemasters.com",
        "author": "Pedro López",
        "category": "productivity",
        "image_url": "https://images.unsplash.com/photo-1506784983877-45594efa4cbe?auto=format&fit=crop&w=1400&q=85",
    },
]


@router.get("")
async def get_articles(category: Optional[str] = Query(None), limit: int = 20):
    """Get articles with images, preferring a public source and falling back to curated content."""
    external_articles = await fetch_external_articles(category, limit)
    source_articles = external_articles if external_articles else ARTICLES

    filtered = source_articles
    if category and category != "Todos":
        filtered = [article for article in source_articles if article["category"] == category]

    result = []
    for index, item in enumerate(filtered[:limit]):
        article = {**item}
        article["published_at"] = (datetime.utcnow() - timedelta(days=index)).isoformat()
        article["is_featured"] = index < 3
        article["created_at"] = datetime.utcnow().isoformat()
        article["image_url"] = article.get("image_url") or ARTICLE_IMAGES.get(
            article["category"],
            ARTICLE_IMAGES["wellness"],
        )
        result.append(article)

    return result


async def fetch_external_articles(category: Optional[str], limit: int) -> List[dict]:
    """Fetch public articles with cover images. This endpoint requires no API key."""
    tag_by_category = {
        "wellness": "wellness",
        "productivity": "productivity",
        "health": "health",
        "finance": "finance",
    }
    tag = tag_by_category.get(category or "", "productivity")
    url = f"https://dev.to/api/articles?tag={tag}&per_page={min(limit, 12)}&top=7"

    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
    except Exception:
        return []

    articles = []
    for item in data:
        image_url = item.get("cover_image") or item.get("social_image")
        if not image_url:
            continue

        mapped_category = category if category and category != "Todos" else infer_category(item)
        articles.append(
            {
                "id": f"devto-{item.get('id')}",
                "title": item.get("title") or "Artículo recomendado",
                "excerpt": item.get("description") or "Una lectura seleccionada para mejorar tus hábitos.",
                "source": "DEV Community",
                "source_url": item.get("url") or "https://dev.to",
                "author": (item.get("user") or {}).get("name"),
                "category": mapped_category,
                "image_url": image_url,
            }
        )

    return articles


def infer_category(item: dict) -> str:
    tags = " ".join(item.get("tag_list") or []).lower()
    if "health" in tags or "fitness" in tags:
        return "health"
    if "finance" in tags or "money" in tags:
        return "finance"
    if "wellness" in tags or "mindfulness" in tags:
        return "wellness"
    return "productivity"


@router.get("/saved")
async def get_saved_articles(user_id: str):
    """Get saved articles for user from database."""
    if not supabase:
        return []

    response = supabase.table("saved_articles").select("*, articles(*)").eq("user_id", user_id).execute()
    return response.data if response.data else []


@router.post("/save")
async def save_article(user_id: str, article_id: str):
    """Save article for user."""
    if not supabase:
        return {"success": True}

    existing = (
        supabase.table("saved_articles")
        .select("id")
        .eq("user_id", user_id)
        .eq("article_id", article_id)
        .execute()
    )

    if existing.data:
        return {"success": True, "message": "Already saved"}

    article = next((item for item in ARTICLES if item["id"] == article_id), None)
    if not article and not article_id.startswith("devto-"):
        raise HTTPException(status_code=404, detail="Article not found")

    data = {
        "user_id": user_id,
        "article_id": article_id,
        "saved_at": datetime.utcnow().isoformat(),
    }

    response = supabase.table("saved_articles").insert(data).execute()
    return {"success": True, "data": response.data[0] if response.data else data}


@router.delete("/save")
async def unsave_article(user_id: str, article_id: str):
    """Remove saved article."""
    if not supabase:
        return {"success": True}

    supabase.table("saved_articles").delete().eq("user_id", user_id).eq("article_id", article_id).execute()
    return {"success": True}
