from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class UserProfileUpdate(BaseModel):
    position: Optional[str] = None        # PG|SG|SF|PF|C
    skill_level: Optional[str] = None     # beginner|intermediate|advanced|elite
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    dominant_hand: Optional[str] = None   # left|right
    goals: Optional[list[str]] = None


class UserProfileResponse(BaseModel):
    id: int
    user_id: int
    position: Optional[str]
    skill_level: Optional[str]
    height_cm: Optional[float]
    weight_kg: Optional[float]
    dominant_hand: Optional[str]
    goals: Optional[list[str]]
    updated_at: datetime
    user: UserResponse

    model_config = {"from_attributes": True}
