from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import datetime, timedelta
from app.database import supabase

router = APIRouter()

ARTICLES = [
    {"id": "1", "title": "Cómo crear un hábito en 30 días", "excerpt": "La ciencia detrás de la formación de hábitos.", "source": "Habitly Blog", "source_url": "https://habitly.app/blog", "author": "Equipo Habitly", "category": "wellness"},
    {"id": "2", "title": "El poder del seguimiento visual", "excerpt": "Por qué ver tu progreso aumenta la motivación.", "source": "Productivity Weekly", "source_url": "https://productivityweekly.com", "author": "Sarah Chen", "category": "productivity"},
    {"id": "3", "title": "Meditación para principiantes", "excerpt": "Una guía simple de 5 minutos para meditar.", "source": "Mindful Living", "source_url": "https://mindfulliving.com", "author": "Miguel Santos", "category": "wellness"},
    {"id": "4", "title": "Regla de los 2 minutos", "excerpt": "La técnica más simple contra la procrastinación.", "source": "Dev.to", "source_url": "https://dev.to", "author": "James Clear", "category": "productivity"},
    {"id": "5", "title": "Sueño y aprendizaje", "excerpt": "Cómo el sueño afecta tu capacidad de aprender.", "source": "Neuroscience Daily", "source_url": "https://neurosciencedaily.com", "author": "Dr. Anna Berg", "category": "health"},
    {"id": "6", "title": "El método Pomodoro", "excerpt": "Trabaja en sprints de 25 minutos.", "source": "Lifehacker", "source_url": "https://lifehacker.com", "author": "Laura Mark", "category": "productivity"},
    {"id": "7", "title": "Gratitud diaria", "excerpt": "Por qué escribir 3 cosas por agradecer.", "source": "Psychology Today", "source_url": "https://psychologytoday.com", "author": "Dr. Robert Emmons", "category": "wellness"},
    {"id": "8", "title": "Finanzas personales básicas", "excerpt": "5 hábitos para construir riqueza.", "source": "Finance Guru", "source_url": "https://financeguru.com", "author": "Mark Cuban", "category": "finance"},
    {"id": "9", "title": "Ejercicio matutino", "excerpt": "Los beneficios de hacer ejercicio por la mañana.", "source": "Health Magazine", "source_url": "https://healthmagazine.com", "author": "Dr. Fitness", "category": "health"},
    {"id": "10", "title": "Mindfulness en el trabajo", "excerpt": "Técnicas de mindfulness para aplicar en la oficina.", "source": "WorkLife", "source_url": "https://worklife.com", "author": "Ana García", "category": "wellness"},
    {"id": "11", "title": "Alimentación inteligente", "excerpt": "Comer bien sin complicarte la vida.", "source": "Nutrition Pro", "source_url": "https://nutritionpro.com", "author": "Carlos Ruiz", "category": "health"},
    {"id": "12", "title": "Gestión del tiempo", "excerpt": "Aprende a dominar tu agenda.", "source": "Time Masters", "source_url": "https://timemasters.com", "author": "Pedro López", "category": "productivity"},
]

@router.get("")
async def get_articles(category: Optional[str] = Query(None), limit: int = 20):
    """Get articles with optional category filter"""
    filtered = ARTICLES
    if category and category != "Todos":
        filtered = [a for a in ARTICLES if a["category"] == category]
    
    result = []
    for i, a in enumerate(filtered[:limit]):
        article = {**a}
        article["published_at"] = (datetime.utcnow() - timedelta(days=i)).isoformat()
        article["is_featured"] = i < 3
        article["created_at"] = datetime.utcnow().isoformat()
        result.append(article)
    
    return result

@router.get("/saved")
async def get_saved_articles(user_id: str):
    """Get saved articles for user from database"""
    if not supabase:
        return []
    
    response = supabase.table("saved_articles").select(
        "*, articles(*)"
    ).eq("user_id", user_id).execute()
    
    return response.data if response.data else []

@router.post("/save")
async def save_article(user_id: str, article_id: str):
    """Save article for user"""
    if not supabase:
        return {"success": True}
    
    # Check if already saved
    existing = supabase.table("saved_articles").select("id").eq("user_id", user_id).eq("article_id", article_id).execute()
    
    if existing.data:
        return {"success": True, "message": "Already saved"}
    
    # Find article
    article = next((a for a in ARTICLES if a["id"] == article_id), None)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Save to database
    data = {
        "user_id": user_id,
        "article_id": article_id,
        "saved_at": datetime.utcnow().isoformat()
    }
    
    response = supabase.table("saved_articles").insert(data).execute()
    return {"success": True, "data": response.data[0] if response.data else data}

@router.delete("/save")
async def unsave_article(user_id: str, article_id: str):
    """Remove saved article"""
    if not supabase:
        return {"success": True}
    
    response = supabase.table("saved_articles").delete().eq("user_id", user_id).eq("article_id", article_id).execute()
    return {"success": True}