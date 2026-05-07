from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UserResponse(BaseModel):
    id: str
    email: str
    fullname: str
    role: str
    language_preference: str = "vi"
    is_active: bool = True
    created_at: Optional[datetime] = None
    phone: Optional[str] = None
    birthYear: Optional[int] = None
    gender: Optional[str] = None
    school: Optional[str] = None
    grade: Optional[str] = None
    bio: Optional[str] = None