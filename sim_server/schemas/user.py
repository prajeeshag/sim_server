from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class UserRead(BaseModel):
    id: UUID
    email: EmailStr
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserProfileRead(BaseModel):
    display_name: str
    avatar_url: str | None
    bio: str | None
    timezone: str
    locale: str
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserProfileUpdate(BaseModel):
    display_name: str | None = None
    avatar_url: str | None = None
    bio: str | None = None
    timezone: str | None = Field(None, max_length=50)
    locale: str | None = Field(None, max_length=10)


class UserReadWithProfile(UserRead):
    profile: UserProfileRead | None = None


class OAuthAccountRead(BaseModel):
    id: UUID
    provider: str
    provider_user_id: str
    expires_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
