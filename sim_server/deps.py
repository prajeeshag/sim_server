from database import TortoiseUserRepository, UserRepository
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from models.schemas import UserInDB
from tokens import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ── Repository Dependency ───────────────────────────────────────────────────
# Swap TortoiseUserRepository with InMemoryUserRepository for tests


async def get_user_repo() -> UserRepository:
    return TortoiseUserRepository()


# ── Current User ────────────────────────────────────────────────────────────


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    repo: UserRepository = Depends(get_user_repo),
) -> UserInDB:
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise ValueError("Not an access token")
        username: str | None = payload.get("sub")
        if not username:
            raise ValueError("Missing subject")
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await repo.get_by_username(username)
    if not user or user.disabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User inactive or not found",
        )
    return user


# ── Active User Guard ───────────────────────────────────────────────────────


async def require_active_user(
    current_user: UserInDB = Depends(get_current_user),
) -> UserInDB:
    if current_user.disabled:
        raise HTTPException(status_code=403, detail="Account is disabled")
    return current_user
