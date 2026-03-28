from database import UserRepository
from deps import get_current_user, get_user_repo
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError
from models.schemas import RefreshRequest, TokenResponse, UserCreate, UserPublic
from security import hash_password, needs_rehash, verify_password
from tokens import create_access_token, create_refresh_token, decode_token

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserPublic, status_code=201)
async def register(
    data: UserCreate,
    repo: UserRepository = Depends(get_user_repo),
):
    if await repo.exists(data.username):
        raise HTTPException(status_code=409, detail="Username already taken")
    return await repo.create(data)


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    repo: UserRepository = Depends(get_user_repo),
):
    user = await repo.get_by_username(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if needs_rehash(user.hashed_password):
        await repo.update_password(user.username, hash_password(form_data.password))

    return TokenResponse(
        access_token=create_access_token(user.username),
        refresh_token=create_refresh_token(user.username),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    body: RefreshRequest,
    repo: UserRepository = Depends(get_user_repo),
):
    try:
        payload = decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise ValueError
        username: str = payload["sub"]
    except (JWTError, ValueError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user = await repo.get_by_username(username)
    if not user or user.disabled:
        raise HTTPException(status_code=403, detail="User not found or disabled")

    return TokenResponse(
        access_token=create_access_token(username),
        refresh_token=create_refresh_token(username),
    )


@router.get("/me", response_model=UserPublic)
async def get_me(current_user: UserPublic = Depends(get_current_user)):
    return current_user
