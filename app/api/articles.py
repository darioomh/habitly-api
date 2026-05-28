from datetime import datetime, timedelta
from typing import List, Optional
import random

import httpx
from fastapi import APIRouter, HTTPException, Query

from app.database import supabase

router = APIRouter()

ARTICLE_IMAGES = {
    "wellness": "https://images.unsplash.com/photo-1506126613408-eca07ce68773?auto=format&fit=crop&w=1400&q=85",
    "productivity": "https://images.unsplash.com/photo-1497366754035-f200968a6e72?auto=format&fit=crop&w=1400&q=85",
    "health": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=1400&q=85",
    "finance": "https://images.unsplash.com/photo-1554224154-26032ffc0d07?auto=format&fit=crop&w=1400&q=85",
}

WEEKLY_ROTATION_SETS = {
    0: "set_a",
    1: "set_b",
    2: "set_c",
    3: "set_d",
}

def get_active_set() -> str:
    week_number = datetime.utcnow().isocalendar()[1]
    return WEEKLY_ROTATION_SETS.get(week_number % 4, "set_a")

ARTICLES_DB = {
    "set_a": [
        {
            "id": "a1", "title": "Cómo construir una rutina matutina imbatible",
            "excerpt": "Descubre los pasos clave para diseñar una mañana que potencie tu productividad y bienestar durante todo el día.",
            "source": "Habitly Journal", "source_url": "https://habitly.app/blog/rutina-matutina",
            "author": "Ana Torres", "category": "productivity",
            "image_url": "https://images.unsplash.com/photo-1506126613408-eca07ce68773?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "a2", "title": "Meditación guiada para reducir la ansiedad",
            "excerpt": "Una práctica de 10 minutos para calmar tu mente y reducir el estrés acumulado del día.",
            "source": "Mindful Living", "source_url": "https://mindfulliving.com/meditacion-ansiedad",
            "author": "Carlos Mendoza", "category": "wellness",
            "image_url": "https://images.unsplash.com/photo-1508672019048-805c876b67e2?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "a3", "title": "Alimentación consciente: come con atención plena",
            "excerpt": "Aprende a aplicar mindfulness a tus comidas para mejorar tu relación con la comida y tu digestión.",
            "source": "Nutrition Pro", "source_url": "https://nutritionpro.com/alimentacion-consciente",
            "author": "María Fernanda Ruiz", "category": "health",
            "image_url": "https://images.unsplash.com/photo-1498837167922-ddd27525d352?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "a4", "title": "Ahorrar sin sacrificios: el método de los 3 sobres",
            "excerpt": "Un sistema simple de finanzas personales que te permite ahorrar sin sentir que te estás privando.",
            "source": "Finance Field Notes", "source_url": "https://financeguru.com/metodo-3-sobres",
            "author": "Laura Jiménez", "category": "finance",
            "image_url": "https://images.unsplash.com/photo-1554224154-26032ffc0d07?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "a5", "title": "El poder del journaling diario",
            "excerpt": "Escribir tres páginas cada mañana puede transformar tu claridad mental y tu creatividad.",
            "source": "Psychology Today", "source_url": "https://psychologytoday.com/journaling-poder",
            "author": "Dr. Robert Emmons", "category": "wellness",
            "image_url": "https://images.unsplash.com/photo-1517842645767-c639042777db?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "a6", "title": "Entrenamiento HIIT de 15 minutos sin equipo",
            "excerpt": "Rutina de alta intensidad para quemar calorías y mejorar tu condición física sin salir de casa.",
            "source": "Fitness Pro", "source_url": "https://fitnesspro.com/hiit-15-min",
            "author": "Pedro Sánchez", "category": "health",
            "image_url": "https://images.unsplash.com/photo-1518611012118-696072aa579a?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "a7", "title": "Técnica Pomodoro para equipos remotos",
            "excerpt": "Cómo adaptar el método Pomodoro para trabajar en equipo de forma sincronizada desde casa.",
            "source": "Remote Work Hub", "source_url": "https://remoteworkhub.com/pomodoro-equipos",
            "author": "Sofía García", "category": "productivity",
            "image_url": "https://images.unsplash.com/photo-1497366811353-6870744d04b2?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "a8", "title": "Inversiones para principiantes: por dónde empezar",
            "excerpt": "Guía básica para dar tus primeros pasos en el mundo de las inversiones con confianza.",
            "source": "Investor 101", "source_url": "https://investor101.com/principiantes",
            "author": "Mark Cuban", "category": "finance",
            "image_url": "https://images.unsplash.com/photo-1560472354-b33dd0b9985c?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "a9", "title": "Cómo dormir mejor según la ciencia",
            "excerpt": "7 estrategias basadas en evidencia para mejorar la calidad de tu sueño y despertar renovado.",
            "source": "Sleep Science", "source_url": "https://sleepscience.com/dormir-mejor",
            "author": "Dra. Anna Berg", "category": "health",
            "image_url": "https://images.unsplash.com/photo-1541781774459-bb2af2f05b55?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "a10", "title": "Minimalismo digital: recupera tu tiempo",
            "excerpt": "Estrategias para reducir el tiempo frente a pantallas y enfocarte en lo que realmente importa.",
            "source": "Digital Detox", "source_url": "https://digitaldetox.com/minimalismo",
            "author": "Luis Martínez", "category": "wellness",
            "image_url": "https://images.unsplash.com/photo-1499750310107-5fef28a66643?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "a11", "title": "Ley de Parkinson: cómo hacer más en menos tiempo",
            "excerpt": "El trabajo se expande hasta ocupar el tiempo disponible. Aprende a usar este principio a tu favor.",
            "source": "Productivity Weekly", "source_url": "https://productivityweekly.com/parkinson",
            "author": "James Clear", "category": "productivity",
            "image_url": "https://images.unsplash.com/photo-1484480974693-6ca0a78fb36b?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "a12", "title": "Yoga para principiantes: posturas esenciales",
            "excerpt": "Las 5 posturas básicas de yoga que todo principiante debe conocer para empezar su práctica.",
            "source": "Yoga Flow", "source_url": "https://yogaflow.com/principiantes",
            "author": "Elena Vega", "category": "wellness",
            "image_url": "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "a13", "title": "Cómo crear un fondo de emergencia",
            "excerpt": "Pasos prácticos para construir un colchón financiero que te dé tranquilidad ante imprevistos.",
            "source": "Finance Guru", "source_url": "https://financeguru.com/fondo-emergencia",
            "author": "Laura Jiménez", "category": "finance",
            "image_url": "https://images.unsplash.com/photo-1579621970563-ebec7560ff3e?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "a14", "title": "Ejercicio de respiración 4-7-8 para dormir",
            "excerpt": "Una técnica simple de respiración que te ayuda a conciliar el sueño en menos de 5 minutos.",
            "source": "Breath Work", "source_url": "https://breathwork.com/4-7-8",
            "author": "Dr. Andrew Weil", "category": "health",
            "image_url": "https://images.unsplash.com/photo-1506126613408-eca07ce68773?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "a15", "title": "Cómo dejar la procrastinación para siempre",
            "excerpt": "Estrategias basadas en psicología conductual para vencer la procrastinación de forma definitiva.",
            "source": "Habit Design", "source_url": "https://jamesclear.com/procrastination",
            "author": "James Clear", "category": "productivity",
            "image_url": "https://images.unsplash.com/photo-1434030216411-0b793f4b4173?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "a16", "title": "Beneficios del ayuno intermitente",
            "excerpt": "Qué dice la ciencia sobre el ayuno intermitente y cómo implementarlo de forma segura.",
            "source": "Health Science", "source_url": "https://healthscience.com/ayuno-intermitente",
            "author": "Dra. María Pérez", "category": "health",
            "image_url": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "a17", "title": "Cómo organizar tu semana en 30 minutos",
            "excerpt": "Un sistema semanal de planificación que te ahorrará horas y reducirá tu estrés.",
            "source": "Time Masters", "source_url": "https://timemasters.com/semana-30min",
            "author": "David Allen", "category": "productivity",
            "image_url": "https://images.unsplash.com/photo-1506784983877-45594efa4cbe?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "a18", "title": "Caminar 10.000 pasos: mito o realidad",
            "excerpt": "Analizamos la evidencia detrás de la meta de los 10.000 pasos diarios y cómo adaptarla a ti.",
            "source": "Fitness Science", "source_url": "https://fitnesscience.com/10000-pasos",
            "author": "Dr. Fitness", "category": "health",
            "image_url": "https://images.unsplash.com/photo-1476480862126-209bfaa8edc8?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "a19", "title": "Gratitud diaria: el hábito que cambia tu cerebro",
            "excerpt": "La práctica de escribir 3 cosas por las que estás agradecido puede reconfigurar tu cerebro para ser más feliz.",
            "source": "Positive Psychology", "source_url": "https://positivepsych.com/gratitud",
            "author": "Dr. Robert Emmons", "category": "wellness",
            "image_url": "https://images.unsplash.com/photo-1489710437720-ebb67ec84dd2?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "a20", "title": "Presupuesto base cero explicado simple",
            "excerpt": "El método de presupuesto que te obliga a justificar cada gasto y tomar control de tu dinero.",
            "source": "Money Smart", "source_url": "https://moneysmart.com/presupuesto-cero",
            "author": "Dave Ramsey", "category": "finance",
            "image_url": "https://images.unsplash.com/photo-1554224155-6726b3ff858f?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "a21", "title": "Cómo leer más libros este año",
            "excerpt": "Estrategias prácticas para duplicar tu cantidad de lectura sin sacrificar tu tiempo.",
            "source": "Learning Lab", "source_url": "https://learninglab.com/leer-mas",
            "author": "Ryan Holiday", "category": "productivity",
            "image_url": "https://images.unsplash.com/photo-1524995997946-a1c2e315a42f?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "a22", "title": "Estiramientos para oficina: 5 minutos",
            "excerpt": "Rutina rápida de estiramientos para hacer en tu escritorio y evitar dolores musculares.",
            "source": "Ergo Work", "source_url": "https://ergowork.com/estiramientos-oficina",
            "author": "Fisio Center", "category": "health",
            "image_url": "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "a23", "title": "Cómo decir que no sin sentir culpa",
            "excerpt": "Aprende a establecer límites saludables en tu vida personal y profesional.",
            "source": "Psychology Today", "source_url": "https://psychologytoday.com/decir-no",
            "author": "Dra. Ana García", "category": "wellness",
            "image_url": "https://images.unsplash.com/photo-1499209974431-9dddcece7f88?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "a24", "title": "Inversión en ETFs para principiantes",
            "excerpt": "Todo lo que necesitas saber sobre ETFs para empezar a invertir de forma diversificada y segura.",
            "source": "Investor 101", "source_url": "https://investor101.com/etfs",
            "author": "Warren Buffet Jr", "category": "finance",
            "image_url": "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "a25", "title": "Cómo mantener la motivación a largo plazo",
            "excerpt": "La motivación no es un sentimiento, es un sistema. Descubre cómo construir el tuyo.",
            "source": "Habitly Journal", "source_url": "https://habitly.app/blog/motivacion",
            "author": "James Clear", "category": "productivity",
            "image_url": "https://images.unsplash.com/photo-1491438590914-bc09fcaaf77a?auto=format&fit=crop&w=1400&q=85",
        },
    ],
    "set_b": [
        {
            "id": "b1", "title": "La ciencia del hábito: cómo funciona tu cerebro",
            "excerpt": "Entiende el bucle del hábito (señal, rutina, recompensa) y úsalo para crear cambios duraderos.",
            "source": "Neuroscience Daily", "source_url": "https://neurosciencedaily.com/ciencia-habito",
            "author": "Dr. Andrew Huberman", "category": "wellness",
            "image_url": "https://images.unsplash.com/photo-1559757175-5700dde675bc?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "b2", "title": "Cómo iniciar un negocio secundario",
            "excerpt": "Pasos concretos para lanzar tu side hustle sin descuidar tu trabajo principal.",
            "source": "Entrepreneur Mind", "source_url": "https://entrepreneurmind.com/side-hustle",
            "author": "Gary Vaynerchuk", "category": "finance",
            "image_url": "https://images.unsplash.com/photo-1559136555-9303baea8ebd?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "b3", "title": "Running para principiantes: plan C25K",
            "excerpt": "El plan Couch to 5K te lleva de cero a correr 5km en 8 semanas. Aquí te explicamos cómo.",
            "source": "Running World", "source_url": "https://runningworld.com/c25k",
            "author": "Elena Vega", "category": "health",
            "image_url": "https://images.unsplash.com/photo-1476480862126-209bfaa8edc8?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "b4", "title": "Deep work: cómo alcanzar el enfoque profundo",
            "excerpt": "El trabajo profundo es el superpoder del siglo XXI. Aprende a cultivarlo y protegerlo.",
            "source": "Productivity Weekly", "source_url": "https://productivityweekly.com/deep-work",
            "author": "Cal Newport", "category": "productivity",
            "image_url": "https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "b5", "title": "Beneficios del té verde para la salud",
            "excerpt": "Descubre por qué el té verde es considerado uno de los superalimentos más completos.",
            "source": "Nutrition Pro", "source_url": "https://nutritionpro.com/te-verde",
            "author": "María Fernanda Ruiz", "category": "health",
            "image_url": "https://images.unsplash.com/photo-1556679343-c7306c1976bc?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "b6", "title": "Cómo crear un sistema de ahorro automático",
            "excerpt": "Automatiza tus ahorros para que no tengas que pensar en ellos. El método más efectivo.",
            "source": "Finance Guru", "source_url": "https://financeguru.com/ahorro-automatico",
            "author": "Laura Jiménez", "category": "finance",
            "image_url": "https://images.unsplash.com/photo-1579621970563-ebec7560ff3e?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "b7", "title": "Mindfulness para principiantes: guía completa",
            "excerpt": "Todo lo que necesitas saber para empezar tu práctica de mindfulness desde cero.",
            "source": "Mindful Living", "source_url": "https://mindfulliving.com/mindfulness-guia",
            "author": "Miguel Santos", "category": "wellness",
            "image_url": "https://images.unsplash.com/photo-1508672019048-805c876b67e2?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "b8", "title": "Cómo organizar tu bandeja de entrada",
            "excerpt": "El método Inbox Zero explicado paso a paso para que nunca más te abrume el correo.",
            "source": "Productivity Lab", "source_url": "https://productivitylab.com/inbox-zero",
            "author": "David Allen", "category": "productivity",
            "image_url": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "b9", "title": "Postura correcta al trabajar en casa",
            "excerpt": "Guía de ergonomía para configurar tu home office y evitar dolores de espalda y cuello.",
            "source": "Ergo Work", "source_url": "https://ergowork.com/postura-home-office",
            "author": "Fisio Center", "category": "health",
            "image_url": "https://images.unsplash.com/photo-1497366754035-f200968a6e72?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "b10", "title": "El método Kaizen: mejora continua",
            "excerpt": "Pequeños cambios diarios que generan grandes resultados a largo plazo. El poder de la mejora del 1%.",
            "source": "Habit Design", "source_url": "https://jamesclear.com/kaizen",
            "author": "James Clear", "category": "productivity",
            "image_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "b11", "title": "Bondad y salud: cómo ayudar mejora tu vida",
            "excerpt": "Estudios muestran que realizar actos de bondad regularmente mejora tu salud física y mental.",
            "source": "Positive Psychology", "source_url": "https://positivepsych.com/bondad-salud",
            "author": "Dra. Sonja Lyubomirsky", "category": "wellness",
            "image_url": "https://images.unsplash.com/photo-1489710437720-ebb67ec84dd2?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "b12", "title": "Cómo negociar tu salario como un profesional",
            "excerpt": "Técnicas de negociación para conseguir el salario que mereces sin sentirte incómodo.",
            "source": "Career Pro", "source_url": "https://careerpro.com/negociar-salario",
            "author": "Sofía García", "category": "finance",
            "image_url": "https://images.unsplash.com/photo-1559136555-9303baea8ebd?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "b13", "title": "Cómo mejorar tu flexibilidad en 10 minutos al día",
            "excerpt": "Rutina diaria de estiramientos para mejorar tu flexibilidad y prevenir lesiones.",
            "source": "Fitness Pro", "source_url": "https://fitnesspro.com/flexibilidad",
            "author": "Pedro Sánchez", "category": "health",
            "image_url": "https://images.unsplash.com/photo-1518611012118-696072aa579a?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "b14", "title": "La regla de los 5 segundos para tomar acción",
            "excerpt": "Cuando tengas el impulso de actuar algo, cuenta 5-4-3-2-1 y muévete antes de que tu cerebro lo detenga.",
            "source": "Motivation Daily", "source_url": "https://motivationdaily.com/5-segundos",
            "author": "Mel Robbins", "category": "productivity",
            "image_url": "https://images.unsplash.com/photo-1434030216411-0b793f4b4173?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "b15", "title": "Caminata consciente: meditación en movimiento",
            "excerpt": "Transforma tu caminata diaria en una práctica de mindfulness con estos simples pasos.",
            "source": "Mindful Living", "source_url": "https://mindfulliving.com/caminata-consciente",
            "author": "Miguel Santos", "category": "wellness",
            "image_url": "https://images.unsplash.com/photo-1476480862126-209bfaa8edc8?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "b16", "title": "Cómo construir un portafolio de inversión",
            "excerpt": "Principios básicos para construir un portafolio diversificado según tu perfil de riesgo.",
            "source": "Investor 101", "source_url": "https://investor101.com/portafolio",
            "author": "Mark Cuban", "category": "finance",
            "image_url": "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "b17", "title": "Cómo tomar agua suficiente cada día",
            "excerpt": "Estrategias simples para mantenerte hidratado sin tener que pensar en ello.",
            "source": "Health Magazine", "source_url": "https://healthmagazine.com/hidratacion",
            "author": "Dra. María Pérez", "category": "health",
            "image_url": "https://images.unsplash.com/photo-1548839140-29a749e1cf4d?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "b18", "title": "Cómo crear un segundo cerebro con notas",
            "excerpt": "El sistema PARA de Tiago Forte para organizar tu conocimiento y liberar tu mente.",
            "source": "Learning Lab", "source_url": "https://learninglab.com/segundo-cerebro",
            "author": "Tiago Forte", "category": "productivity",
            "image_url": "https://images.unsplash.com/photo-1455390582262-044cdead277a?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "b19", "title": "Aprende a cocinar saludable en 1 semana",
            "excerpt": "Plan de comidas semanal para aprender lo básico de cocina saludable sin estrés.",
            "source": "Nutrition Pro", "source_url": "https://nutritionpro.com/cocina-saludable",
            "author": "Carlos Ruiz", "category": "health",
            "image_url": "https://images.unsplash.com/photo-1498837167922-ddd27525d352?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "b20", "title": "Los 4 acuerdos: guía práctica",
            "excerpt": "Aplica los principios del libro de Miguel Ruiz a tu vida diaria para encontrar paz interior.",
            "source": "Psychology Today", "source_url": "https://psychologytoday.com/4-acuerdos",
            "author": "Miguel Ruiz", "category": "wellness",
            "image_url": "https://images.unsplash.com/photo-1499209974431-9dddcece7f88?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "b21", "title": "Interés compuesto: el octavo milagro del mundo",
            "excerpt": "Cómo el interés compuesto puede convertir ahorros pequeños en una fortuna con el tiempo.",
            "source": "Finance Field Notes", "source_url": "https://financeguru.com/interes-compuesto",
            "author": "Albert Einstein", "category": "finance",
            "image_url": "https://images.unsplash.com/photo-1560472354-b33dd0b9985c?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "b22", "title": "Cómo dejar de compararte con los demás",
            "excerpt": "Estrategias para superar la trampa de la comparación y enfocarte en tu propio progreso.",
            "source": "Psychology Today", "source_url": "https://psychologytoday.com/dejar-comparar",
            "author": "Dra. Ana García", "category": "wellness",
            "image_url": "https://images.unsplash.com/photo-1517842645767-c639042777db?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "b23", "title": "Inteligencia emocional en el trabajo",
            "excerpt": "Desarrolla tu inteligencia emocional para mejorar tus relaciones laborales y tu liderazgo.",
            "source": "WorkLife", "source_url": "https://worklife.com/ie-trabajo",
            "author": "Daniel Goleman", "category": "productivity",
            "image_url": "https://images.unsplash.com/photo-1497366811353-6870744d04b2?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "b24", "title": "Cómo prepararte para una maratón",
            "excerpt": "Plan de entrenamiento de 16 semanas para completar tu primera maratón de forma segura.",
            "source": "Running World", "source_url": "https://runningworld.com/maraton",
            "author": "Elena Vega", "category": "health",
            "image_url": "https://images.unsplash.com/photo-1513593771513-7b58b6c4af76?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "b25", "title": "Cómo practicar la escucha activa",
            "excerpt": "Mejora tus relaciones personales y profesionales con la técnica de la escucha activa.",
            "source": "Communication Pro", "source_url": "https://communicationpro.com/escucha-activa",
            "author": "Sofía García", "category": "wellness",
            "image_url": "https://images.unsplash.com/photo-1529156069898-49953e39b3ac?auto=format&fit=crop&w=1400&q=85",
        },
    ],
    "set_c": [
        {
            "id": "c1", "title": "Cómo vencer la pereza y tomar acción",
            "excerpt": "La pereza no es falta de disciplina, es falta de claridad. Descubre cómo superarla.",
            "source": "Habitly Journal", "source_url": "https://habitly.app/blog/vencer-pereza",
            "author": "Ana Torres", "category": "productivity",
            "image_url": "https://images.unsplash.com/photo-1434030216411-0b793f4b4173?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "c2", "title": "Los beneficios del baño de bosque",
            "excerpt": "Shinrin-yoku: la práctica japonesa de sumergirse en la naturaleza tiene beneficios científicamente probados.",
            "source": "Nature Health", "source_url": "https://naturehealth.com/bano-bosque",
            "author": "Dr. Qing Li", "category": "wellness",
            "image_url": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "c3", "title": "La dieta mediterránea explicada",
            "excerpt": "Por qué la dieta mediterránea es considerada la más saludable del mundo por los expertos.",
            "source": "Nutrition Pro", "source_url": "https://nutritionpro.com/dieta-mediterranea",
            "author": "Dra. María Pérez", "category": "health",
            "image_url": "https://images.unsplash.com/photo-1498837167922-ddd27525d352?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "c4", "title": "Cómo reducir gastos sin dolor",
            "excerpt": "52 pequeños cambios que reducen tus gastos sin que sientas que estás sacrificando tu estilo de vida.",
            "source": "Money Smart", "source_url": "https://moneysmart.com/reducir-gastos",
            "author": "Laura Jiménez", "category": "finance",
            "image_url": "https://images.unsplash.com/photo-1554224154-26032ffc0d07?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "c5", "title": "Lectura rápida: cómo leer el doble",
            "excerpt": "Técnicas de lectura rápida que puedes aprender hoy para procesar más información en menos tiempo.",
            "source": "Learning Lab", "source_url": "https://learninglab.com/lectura-rapida",
            "author": "Tim Ferriss", "category": "productivity",
            "image_url": "https://images.unsplash.com/photo-1524995997946-a1c2e315a42f?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "c6", "title": "Cómo el ejercicio mejora tu memoria",
            "excerpt": "La conexión entre el ejercicio físico y la función cognitiva, explicada por la neurociencia.",
            "source": "Brain Health", "source_url": "https://brainhealth.com/ejercicio-memoria",
            "author": "Dr. Andrew Huberman", "category": "health",
            "image_url": "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "c7", "title": "Cómo empezar un diario de gratitud",
            "excerpt": "Guía paso a paso para crear y mantener un diario de gratitud que transforme tu perspectiva.",
            "source": "Positive Psychology", "source_url": "https://positivepsych.com/diario-gratitud",
            "author": "Dr. Robert Emmons", "category": "wellness",
            "image_url": "https://images.unsplash.com/photo-1489710437720-ebb67ec84dd2?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "c8", "title": "Freelance: cómo fijar tus tarifas",
            "excerpt": "Aprende a calcular el valor de tu trabajo y establecer tarifas que reflejen tu verdadero valor.",
            "source": "Career Pro", "source_url": "https://careerpro.com/tarifas-freelance",
            "author": "Sofía García", "category": "finance",
            "image_url": "https://images.unsplash.com/photo-1559136555-9303baea8ebd?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "c9", "title": "Cómo dejar el azúcar en 30 días",
            "excerpt": "Un plan de desintoxicación de azúcar de 30 días con alternativas saludables y deliciosas.",
            "source": "Health Magazine", "source_url": "https://healthmagazine.com/dejar-azucar",
            "author": "Dr. Fitness", "category": "health",
            "image_url": "https://images.unsplash.com/photo-1551963831-b3b1ca40c98e?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "c10", "title": "Cómo hacer networking de verdad",
            "excerpt": "Construye relaciones profesionales auténticas que abran puertas sin sentirte falso.",
            "source": "Career Pro", "source_url": "https://careerpro.com/networking-real",
            "author": "Keith Ferrazzi", "category": "productivity",
            "image_url": "https://images.unsplash.com/photo-1529156069898-49953e39b3ac?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "c11", "title": "Respiración Wim Hof para principiantes",
            "excerpt": "El método de respiración de Wim Hof puede mejorar tu energía, reducir el estrés y fortalecer tu sistema inmune.",
            "source": "Breath Work", "source_url": "https://breathwork.com/wim-hof",
            "author": "Wim Hof", "category": "wellness",
            "image_url": "https://images.unsplash.com/photo-1506126613408-eca07ce68773?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "c12", "title": "Inversión en bienes raíces desde cero",
            "excerpt": "Cómo empezar a invertir en propiedades sin tener millones, desde la teoría hasta la práctica.",
            "source": "Real Estate 101", "source_url": "https://realestate101.com/bienes-raices",
            "author": "Robert Kiyosaki", "category": "finance",
            "image_url": "https://images.unsplash.com/photo-1560520031-3a4dc695e2e1?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "c13", "title": "Cómo tener más energía durante el día",
            "excerpt": "Estrategias basadas en ciencia para mantener altos niveles de energía sin recurrir a la cafeína.",
            "source": "Health Science", "source_url": "https://healthscience.com/mas-energia",
            "author": "Dr. Andrew Huberman", "category": "health",
            "image_url": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "c14", "title": "La técnica GTD explicada simple",
            "excerpt": "Getting Things Done de David Allen, explicado en pasos simples para que puedas aplicarlo hoy.",
            "source": "Productivity Weekly", "source_url": "https://productivityweekly.com/gtd-simple",
            "author": "David Allen", "category": "productivity",
            "image_url": "https://images.unsplash.com/photo-1484480974693-6ca0a78fb36b?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "c15", "title": "Cómo crear un santuario en tu hogar",
            "excerpt": "Transforma tu espacio vital en un refugio de paz y tranquilidad con diseño consciente.",
            "source": "Mindful Living", "source_url": "https://mindfulliving.com/santuario-hogar",
            "author": "Marie Kondo", "category": "wellness",
            "image_url": "https://images.unsplash.com/photo-1484101403633-562f891dc89a?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "c16", "title": "Cómo ahorrar para la jubilación desde joven",
            "excerpt": "El poder de empezar a ahorrar para tu retiro a los 20 vs 30 vs 40 años. La diferencia es brutal.",
            "source": "Finance Guru", "source_url": "https://financeguru.com/jubilacion-joven",
            "author": "Dave Ramsey", "category": "finance",
            "image_url": "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "c17", "title": "Fortaleza mental: cómo desarrollarla",
            "excerpt": "Ejercicios prácticos para desarrollar resiliencia mental y enfrentar desafíos con determinación.",
            "source": "Psychology Today", "source_url": "https://psychologytoday.com/fortaleza-mental",
            "author": "Angela Duckworth", "category": "wellness",
            "image_url": "https://images.unsplash.com/photo-1499209974431-9dddcece7f88?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "c18", "title": "Qué comer antes y después de entrenar",
            "excerpt": "Guía de nutrición deportiva para maximizar tu rendimiento y recuperación muscular.",
            "source": "Fitness Pro", "source_url": "https://fitnesspro.com/comer-entrenar",
            "author": "Carlos Ruiz", "category": "health",
            "image_url": "https://images.unsplash.com/photo-1517836357463-d25dfeac3438?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "c19", "title": "Cómo hacer una revisión semanal efectiva",
            "excerpt": "La revisión semanal es el hábito clave que separa a los productivos de los que solo están ocupados.",
            "source": "Time Masters", "source_url": "https://timemasters.com/revision-semanal",
            "author": "David Allen", "category": "productivity",
            "image_url": "https://images.unsplash.com/photo-1506784983877-45594efa4cbe?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "c20", "title": "Cómo cultivar la paciencia en un mundo rápido",
            "excerpt": "Estrategias para desarrollar paciencia en la era de la gratificación instantánea.",
            "source": "Mindful Living", "source_url": "https://mindfulliving.com/paciencia",
            "author": "Miguel Santos", "category": "wellness",
            "image_url": "https://images.unsplash.com/photo-1506126613408-eca07ce68773?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "c21", "title": "Cómo calcular tu tasa de ahorro ideal",
            "excerpt": "Aprende a calcular cuánto deberías ahorrar según tus ingresos, gastos y metas financieras.",
            "source": "Finance Field Notes", "source_url": "https://financeguru.com/tasa-ahorro",
            "author": "Laura Jiménez", "category": "finance",
            "image_url": "https://images.unsplash.com/photo-1554224155-6726b3ff858f?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "c22", "title": "Cómo mejorar tu postura en 7 días",
            "excerpt": "Ejercicios simples y correcciones posturales para mejorar tu alineación en una semana.",
            "source": "Health Magazine", "source_url": "https://healthmagazine.com/mejorar-postura",
            "author": "Fisio Center", "category": "health",
            "image_url": "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "c23", "title": "Cómo tomar mejores decisiones",
            "excerpt": "Un marco de decisión de 4 pasos para tomar mejores decisiones con menos estrés.",
            "source": "Psychology Today", "source_url": "https://psychologytoday.com/mejores-decisiones",
            "author": "Daniel Kahneman", "category": "productivity",
            "image_url": "https://images.unsplash.com/photo-1456406644174-8ddd4cd52a06?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "c24", "title": "Cómo hacer amigos siendo adulto",
            "excerpt": "Hacer amigos en la vida adulta es difícil pero no imposible. Estrategias que funcionan.",
            "source": "Psychology Today", "source_url": "https://psychologytoday.com/amigos-adulto",
            "author": "Dr. Robert Emmons", "category": "wellness",
            "image_url": "https://images.unsplash.com/photo-1529156069898-49953e39b3ac?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "c25", "title": "Natación para principientes adultos",
            "excerpt": "Guía completa para adultos que quieren aprender a nadar o mejorar su técnica.",
            "source": "Fitness Pro", "source_url": "https://fitnesspro.com/natacion",
            "author": "Pedro Sánchez", "category": "health",
            "image_url": "https://images.unsplash.com/photo-1530549387789-4c1017266634?auto=format&fit=crop&w=1400&q=85",
        },
    ],
    "set_d": [
        {
            "id": "d1", "title": "Cómo crear un hábito en 30 días",
            "excerpt": "Basado en el estudio de Lally sobre formación de hábitos, descubre el plan de 30 días que funciona.",
            "source": "Habitly Journal", "source_url": "https://habitly.app/blog/habito-30-dias",
            "author": "Ana Torres", "category": "productivity",
            "image_url": "https://images.unsplash.com/photo-1499209974431-9dddcece7f88?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "d2", "title": "Cómo baños de agua fría mejoran tu salud",
            "excerpt": "Los beneficios de la exposición al frío: inflamación, estado de ánimo, energía y sistema inmune.",
            "source": "Health Science", "source_url": "https://healthscience.com/agua-fria",
            "author": "Dr. Andrew Huberman", "category": "health",
            "image_url": "https://images.unsplash.com/photo-1516339901601-2e1b62dc0c45?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "d3", "title": "Ladrones de tiempo: cómo identificarlos",
            "excerpt": "Las 7 actividades que más tiempo te roban y cómo eliminarlas de tu día.",
            "source": "Productivity Weekly", "source_url": "https://productivityweekly.com/ladrones-tiempo",
            "author": "Cal Newport", "category": "productivity",
            "image_url": "https://images.unsplash.com/photo-1499750310107-5fef28a66643?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "d4", "title": "Cómo crear un home gym con poco presupuesto",
            "excerpt": "Equipa tu gimnasio en casa sin gastar una fortuna. Estas 5 piezas son todo lo que necesitas.",
            "source": "Fitness Pro", "source_url": "https://fitnesspro.com/home-gym-barato",
            "author": "Pedro Sánchez", "category": "health",
            "image_url": "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "d5", "title": "La filosofía Stoica para la vida moderna",
            "excerpt": "Cómo aplicar las enseñanzas de Marco Aurelio, Séneca y Epicteto a los desafíos del siglo XXI.",
            "source": "Philosophy Now", "source_url": "https://philosophynow.com/estoicismo",
            "author": "Ryan Holiday", "category": "wellness",
            "image_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "d6", "title": "Cómo crear múltiples fuentes de ingreso",
            "excerpt": "Estrategias para diversificar tus ingresos y no depender de una sola fuente.",
            "source": "Entrepreneur Mind", "source_url": "https://entrepreneurmind.com/fuentes-ingreso",
            "author": "Gary Vaynerchuk", "category": "finance",
            "image_url": "https://images.unsplash.com/photo-1559136555-9303baea8ebd?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "d7", "title": "Visualización creativa: cómo usarla",
            "excerpt": "La técnica de visualización que usan atletas y CEOs para alcanzar sus metas más ambiciosas.",
            "source": "Peak Performance", "source_url": "https://peakperformance.com/visualizacion",
            "author": "Jimmy Chin", "category": "wellness",
            "image_url": "https://images.unsplash.com/photo-1491438590914-bc09fcaaf77a?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "d8", "title": "Cómo evitar el agotamiento laboral",
            "excerpt": "Señales de alerta del burnout y estrategias para prevenirlo antes de que sea demasiado tarde.",
            "source": "WorkLife", "source_url": "https://worklife.com/evitar-burnout",
            "author": "Sofía García", "category": "health",
            "image_url": "https://images.unsplash.com/photo-1497366811353-6870744d04b2?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "d9", "title": "Cómo usar LinkedIn para tu carrera",
            "excerpt": "Optimiza tu perfil de LinkedIn y construye tu marca personal para atraer oportunidades.",
            "source": "Career Pro", "source_url": "https://careerpro.com/linkedin-carrera",
            "author": "Sofía García", "category": "productivity",
            "image_url": "https://images.unsplash.com/photo-1611926653458-09294b3142bf?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "d10", "title": "Té matcha: beneficios y cómo prepararlo",
            "excerpt": "Descubre por qué el matcha es superior al café y cómo prepararlo correctamente.",
            "source": "Nutrition Pro", "source_url": "https://nutritionpro.com/matcha",
            "author": "Carlos Ruiz", "category": "health",
            "image_url": "https://images.unsplash.com/photo-1556679343-c7306c1976bc?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "d11", "title": "Cómo organizar tus finanzas en pareja",
            "excerpt": "Conversaciones difíciles pero necesarias para manejar el dinero en pareja de forma saludable.",
            "source": "Finance Guru", "source_url": "https://financeguru.com/finanzas-pareja",
            "author": "Laura Jiménez", "category": "finance",
            "image_url": "https://images.unsplash.com/photo-1579621970563-ebec7560ff3e?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "d12", "title": "Cómo caminar descalzo mejora tu salud",
            "excerpt": "Earthing o grounding: la práctica de conectar tu cuerpo con la tierra tiene beneficios sorprendentes.",
            "source": "Nature Health", "source_url": "https://naturehealth.com/caminar-descalzo",
            "author": "Dr. Qing Li", "category": "wellness",
            "image_url": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "d13", "title": "Cómo hacer un detox digital este fin de semana",
            "excerpt": "Plan de 48 horas para desconectarte de las pantallas y reconectar contigo mismo.",
            "source": "Digital Detox", "source_url": "https://digitaldetox.com/detox-fin-semana",
            "author": "Luis Martínez", "category": "wellness",
            "image_url": "https://images.unsplash.com/photo-1499750310107-5fef28a66643?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "d14", "title": "El método Eisenhower para priorizar",
            "excerpt": "La matriz de Eisenhower te ayuda a distinguir entre lo urgente y lo importante. Domínala.",
            "source": "Time Masters", "source_url": "https://timemasters.com/eisenhower",
            "author": "Stephen Covey", "category": "productivity",
            "image_url": "https://images.unsplash.com/photo-1456406644174-8ddd4cd52a06?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "d15", "title": "Cómo mejorar tu digestión naturalmente",
            "excerpt": "Hábitos simples que mejoran tu digestión: desde masticar bien hasta probióticos naturales.",
            "source": "Health Magazine", "source_url": "https://healthmagazine.com/mejorar-digestion",
            "author": "Dra. María Pérez", "category": "health",
            "image_url": "https://images.unsplash.com/photo-1548839140-29a749e1cf4d?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "d16", "title": "Cómo crear un plan financiero anual",
            "excerpt": "Guía paso a paso para diseñar tu plan financiero del año con metas claras y alcanzables.",
            "source": "Money Smart", "source_url": "https://moneysmart.com/plan-financiero-anual",
            "author": "Dave Ramsey", "category": "finance",
            "image_url": "https://images.unsplash.com/photo-1554224155-6726b3ff858f?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "d17", "title": "Cómo mejorar tu autoestima",
            "excerpt": "Ejercicios prácticos basados en terapia cognitivo-conductual para fortalecer tu autoestima.",
            "source": "Psychology Today", "source_url": "https://psychologytoday.com/mejorar-autoestima",
            "author": "Dra. Ana García", "category": "wellness",
            "image_url": "https://images.unsplash.com/photo-1517842645767-c639042777db?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "d18", "title": "Cómo empezar a meditar: guía para escépticos",
            "excerpt": "Si crees que la meditación no es para ti, esta guía está diseñada específicamente para ti.",
            "source": "Mindful Living", "source_url": "https://mindfulliving.com/meditacion-escepticos",
            "author": "Sam Harris", "category": "wellness",
            "image_url": "https://images.unsplash.com/photo-1506126613408-eca07ce68773?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "d19", "title": "Cómo la música afecta tu productividad",
            "excerpt": "Qué tipo de música escuchar mientras trabajas según la tarea que estés realizando.",
            "source": "Neuroscience Daily", "source_url": "https://neurosciencedaily.com/musica-productividad",
            "author": "Dr. Andrew Huberman", "category": "productivity",
            "image_url": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "d20", "title": "Ejercicios de Kegel para hombres y mujeres",
            "excerpt": "Fortalece tu suelo pélvico con estos ejercicios simples que puedes hacer en cualquier lugar.",
            "source": "Health Science", "source_url": "https://healthscience.com/kegel",
            "author": "Dr. Fitness", "category": "health",
            "image_url": "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "d21", "title": "Cómo vender cosas que ya no usas",
            "excerpt": "Guía para ganar dinero extra vendiendo lo que ya no necesitas en plataformas digitales.",
            "source": "Money Smart", "source_url": "https://moneysmart.com/vender-cosas",
            "author": "Laura Jiménez", "category": "finance",
            "image_url": "https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "d22", "title": "Cómo establecer metas SMART que funcionen",
            "excerpt": "El método de metas SMART: específicas, medibles, alcanzables, relevantes y con tiempo definido.",
            "source": "Habitly Journal", "source_url": "https://habitly.app/blog/metas-smart",
            "author": "Ana Torres", "category": "productivity",
            "image_url": "https://images.unsplash.com/photo-1434030216411-0b793f4b4173?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "d23", "title": "Beneficios de tener una planta en tu escritorio",
            "excerpt": "Tener plantas en tu espacio de trabajo reduce el estrés y aumenta la productividad.",
            "source": "WorkLife", "source_url": "https://worklife.com/plantas-escritorio",
            "author": "Sofía García", "category": "wellness",
            "image_url": "https://images.unsplash.com/photo-1484101403633-562f891dc89a?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "d24", "title": "Cómo entrenar con bandas de resistencia",
            "excerpt": "Rutina completa de ejercicios con bandas elásticas para tonificar todo tu cuerpo en casa.",
            "source": "Fitness Pro", "source_url": "https://fitnesspro.com/bandas-resistencia",
            "author": "Pedro Sánchez", "category": "health",
            "image_url": "https://images.unsplash.com/photo-1517836357463-d25dfeac3438?auto=format&fit=crop&w=1400&q=85",
        },
        {
            "id": "d25", "title": "Cómo viajar barato: guía completa",
            "excerpt": "Estrategias para viajar por el mundo sin gastar una fortuna. Consejos de mochileros expertos.",
            "source": "Travel Smart", "source_url": "https://travelsmart.com/viajar-barato",
            "author": "Luis Martínez", "category": "finance",
            "image_url": "https://images.unsplash.com/photo-1488646953014-85cb44e25828?auto=format&fit=crop&w=1400&q=85",
        },
    ],
}


@router.get("")
async def get_articles(category: Optional[str] = Query(None), limit: int = 20):
    """Get articles with weekly rotation and automatic content refresh."""
    active_set = get_active_set()
    source_articles = ARTICLES_DB.get(active_set, ARTICLES_DB["set_a"])

    external_articles = await fetch_external_articles(category, limit)
    if external_articles:
        combined = source_articles + external_articles
    else:
        combined = source_articles

    filtered = combined
    if category and category != "Todos":
        filtered = [article for article in combined if article["category"] == category]

    random.shuffle(filtered)

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

    all_articles = []
    for set_key in ARTICLES_DB:
        all_articles.extend(ARTICLES_DB[set_key])
    article = next((item for item in all_articles if item["id"] == article_id), None)
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
