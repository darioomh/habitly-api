from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# User models
class UserBase(BaseModel):
    email: str
    display_name: Optional[str] = None

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: str
    created_at: datetime

# Habit models
class HabitBase(BaseModel):
    title: str
    description: Optional[str] = None
    category: str = "general"
    frequency: str = "daily"
    target_days: List[int] = [0, 1, 2, 3, 4, 5, 6]
    xp_value: int = 10

class HabitCreate(HabitBase):
    user_id: str

class HabitUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class Habit(HabitBase):
    id: str
    user_id: str
    streak: int = 0
    best_streak: int = 0
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

# Habit Log models
class HabitLogBase(BaseModel):
    habit_id: str
    user_id: str
    date: str
    completed: bool = False
    notes: Optional[str] = None

class HabitLogCreate(HabitLogBase):
    pass

class HabitLog(HabitLogBase):
    id: str
    xp_earned: int = 0
    created_at: datetime

# Article models
class Article(BaseModel):
    id: str
    title: str
    content: Optional[str] = None
    excerpt: Optional[str] = None
    source: str
    source_url: str
    author: Optional[str] = None
    image_url: Optional[str] = None
    category: str = "wellness"
    published_at: datetime
    is_featured: bool = False
    created_at: datetime

# User Preference models
class UserPreferenceBase(BaseModel):
    theme: str = "system"
    notifications: bool = True
    reminder_time: str = "09:00"
    sync_enabled: bool = True

class UserPreferenceUpdate(UserPreferenceBase):
    pass

class UserPreference(UserPreferenceBase):
    id: str
    user_id: str
    updated_at: datetime

# Journal models
class JournalEntryBase(BaseModel):
    user_id: str
    date: str
    mood: str
    note: Optional[str] = None
    habit_reflections: Optional[List[dict]] = None

class JournalEntryCreate(JournalEntryBase):
    pass

class JournalEntry(JournalEntryBase):
    id: str
    created_at: datetime
    updated_at: datetime

class JournalListResponse(BaseModel):
    entries: List[JournalEntry]