from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from sim_server.deps import require_admin
from sim_server.models.audit import LoginAttempt, LoginResult, UserEvent
from sim_server.models.user import Permission, Role, User
from sim_server.schemas import (
    LoginAttemptRead,
    RoleCreate,
    RoleRead,
    UserAdminRead,
    UserEventRead,
    UserRead,
)

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(require_admin)],
)


# ── Users ────────────────────────────────────────────────────────────────────


@router.get("/users", response_model=list[UserAdminRead])
async def list_users(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    users = await User.all().offset(offset).limit(limit).prefetch_related("roles")
    return [
        UserAdminRead(
            **{f: getattr(u, f) for f in UserRead.model_fields},
            roles=[r.name for r in await u.roles.all()],
        )
        for u in users
    ]


@router.get("/users/{user_id}", response_model=UserAdminRead)
async def get_user(user_id: UUID):
    user = await User.get_or_none(id=user_id).prefetch_related("roles")
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return UserAdminRead(
        **{f: getattr(user, f) for f in UserRead.model_fields},
        roles=[r.name for r in await user.roles.all()],
    )


@router.patch("/users/{user_id}/activate", response_model=UserRead)
async def activate_user(user_id: UUID):
    user = await User.get_or_none(id=user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    user.is_active = True
    await user.save()
    return user


@router.patch("/users/{user_id}/deactivate", response_model=UserRead)
async def deactivate_user(user_id: UUID):
    user = await User.get_or_none(id=user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    user.is_active = False
    await user.save()
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: UUID):
    deleted = await User.filter(id=user_id).delete()
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )


# ── Roles ─────────────────────────────────────────────────────────────────────


@router.get("/roles", response_model=list[RoleRead])
async def list_roles():
    return await Role.all().prefetch_related("permissions")


@router.post("/roles", response_model=RoleRead, status_code=status.HTTP_201_CREATED)
async def create_role(data: RoleCreate):
    if await Role.filter(name=data.name).exists():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Role already exists"
        )
    return await Role.create(name=data.name)


@router.delete("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(role_id: int):
    deleted = await Role.filter(id=role_id).delete()
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
        )


@router.post("/roles/{role_id}/permissions/{codename}", response_model=RoleRead)
async def add_permission_to_role(role_id: int, codename: str):
    role = await Role.get_or_none(id=role_id)
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
        )
    perm, _ = await Permission.get_or_create(codename=codename)
    await role.permissions.add(perm)
    await role.fetch_related("permissions")
    return role


@router.delete(
    "/roles/{role_id}/permissions/{codename}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_permission_from_role(role_id: int, codename: str):
    role = await Role.get_or_none(id=role_id)
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
        )
    perm = await Permission.get_or_none(codename=codename)
    if perm is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found"
        )
    await role.permissions.remove(perm)


# ── User ↔ Role ───────────────────────────────────────────────────────────────


@router.post("/users/{user_id}/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def assign_role(user_id: UUID, role_id: int):
    user = await User.get_or_none(id=user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    role = await Role.get_or_none(id=role_id)
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
        )
    await user.roles.add(role)


@router.delete(
    "/users/{user_id}/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_role(user_id: UUID, role_id: int):
    user = await User.get_or_none(id=user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    role = await Role.get_or_none(id=role_id)
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
        )
    await user.roles.remove(role)


# ── Audit ─────────────────────────────────────────────────────────────────────


@router.get("/audit/events", response_model=list[UserEventRead])
async def list_user_events(
    user_id: UUID | None = Query(None),
    event_type: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    qs = UserEvent.all().order_by("-occurred_at")
    if user_id is not None:
        qs = qs.filter(user_id=str(user_id))
    if event_type is not None:
        qs = qs.filter(event_type=event_type)
    rows = (
        await qs.offset(offset)
        .limit(limit)
        .values(
            "id",
            "user_id",
            "event_type",
            "ip_address",
            "user_agent",
            "metadata",
            "occurred_at",
        )
    )
    return [UserEventRead(**r) for r in rows]


@router.get("/audit/login-attempts", response_model=list[LoginAttemptRead])
async def list_login_attempts(
    email: str | None = Query(None),
    ip_address: str | None = Query(None),
    result: LoginResult | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    qs = LoginAttempt.all().order_by("-attempted_at")
    if email is not None:
        qs = qs.filter(email=email)
    if ip_address is not None:
        qs = qs.filter(ip_address=ip_address)
    if result is not None:
        qs = qs.filter(result=result)
    return await qs.offset(offset).limit(limit)
