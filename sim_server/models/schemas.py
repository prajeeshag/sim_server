from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserPublic(BaseModel):
    id: UUID
    username: str
    email: str
    disabled: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserInDB(UserPublic):
    hashed_password: str

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str
