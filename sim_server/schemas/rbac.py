from pydantic import BaseModel, ConfigDict, Field


class PermissionRead(BaseModel):
    id: int
    codename: str

    model_config = ConfigDict(from_attributes=True)


class RoleCreate(BaseModel):
    name: str = Field(max_length=50)


class RoleRead(BaseModel):
    id: int
    name: str
    permissions: list[PermissionRead] = []

    model_config = ConfigDict(from_attributes=True)


class RoleAssign(BaseModel):
    role_name: str
