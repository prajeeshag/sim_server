from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from sim_server.models.audit import EventType, LoginResult


class LoginAttemptRead(BaseModel):
    id: UUID
    email: str
    ip_address: str
    user_agent: str | None
    result: LoginResult
    attempted_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserEventRead(BaseModel):
    id: UUID
    # user_id is the raw FK column — accessed via .values("user_id") from the ORM,
    # or set explicitly when constructing from a dict/values query result.
    user_id: UUID | None
    event_type: EventType
    ip_address: str | None
    user_agent: str | None
    metadata: dict | None
    occurred_at: datetime

    model_config = ConfigDict(from_attributes=True)
