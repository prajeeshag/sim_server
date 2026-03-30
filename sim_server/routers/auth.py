import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from config import settings
from deps import get_current_user
from fastapi import APIRouter, Depends, HTTPException, status
from security import hash_password, verify_password
from tokens import create_access_token

from sim_server.models.user import RefreshToken, TokenPurpose, User, VerificationToken
from sim_server.schemas import (
    EmailVerifyRequest,
    LoginRequest,
    PasswordChangeRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshRequest,
    TokenResponse,
    UserCreate,
    UserRead,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _token_response(user_id: str, raw_refresh: str) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(user_id),
        refresh_token=raw_refresh,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate):
    if await User.filter(email=data.email).exists():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        )

    user = await User.create(
        email=data.email,
        hashed_password=hash_password(data.password),
    )

    raw_token = secrets.token_urlsafe(32)
    await VerificationToken.create(
        user=user,
        token_hash=_hash(raw_token),
        purpose=TokenPurpose.EMAIL_VERIFY,
        expires_at=datetime.now(tz=timezone.utc) + timedelta(hours=24),
    )
    # TODO: send raw_token to user.email

    return user


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest):
    user = await User.get_or_none(email=data.email)
    if user is None or user.hashed_password is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    ok, new_hash = verify_password(data.password, user.hashed_password)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Email not verified"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Account inactive"
        )

    if new_hash is not None:
        user.hashed_password = new_hash
        await user.save()

    raw_refresh = secrets.token_urlsafe(32)
    await RefreshToken.create(
        user=user,
        token_hash=_hash(raw_refresh),
        expires_at=datetime.now(tz=timezone.utc)
        + timedelta(days=settings.refresh_token_expire_days),
    )

    return _token_response(str(user.id), raw_refresh)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshRequest):
    token_hash = _hash(data.refresh_token)
    record = await RefreshToken.get_or_none(token_hash=token_hash).prefetch_related(
        "user"
    )

    if (
        record is None
        or record.revoked
        or record.expires_at < datetime.now(tz=timezone.utc)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    record.revoked = True
    await record.save()

    raw_refresh = secrets.token_urlsafe(32)
    await RefreshToken.create(
        user=record.user,
        token_hash=_hash(raw_refresh),
        expires_at=datetime.now(tz=timezone.utc)
        + timedelta(days=settings.refresh_token_expire_days),
    )

    return _token_response(str(record.user.id), raw_refresh)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(data: RefreshRequest):
    token_hash = _hash(data.refresh_token)
    record = await RefreshToken.get_or_none(token_hash=token_hash)
    if record is not None and not record.revoked:
        record.revoked = True
        await record.save()


@router.post("/verify-email", status_code=status.HTTP_204_NO_CONTENT)
async def verify_email(data: EmailVerifyRequest):
    token_hash = _hash(data.token)
    record = await VerificationToken.get_or_none(
        token_hash=token_hash, purpose=TokenPurpose.EMAIL_VERIFY
    ).prefetch_related("user")

    if (
        record is None
        or record.used_at is not None
        or record.expires_at < datetime.now(tz=timezone.utc)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token"
        )

    record.used_at = datetime.now(tz=timezone.utc)
    await record.save()

    record.user.is_verified = True
    record.user.is_active = True
    await record.user.save()


@router.post("/password-reset/request", status_code=status.HTTP_204_NO_CONTENT)
async def request_password_reset(data: PasswordResetRequest):
    user = await User.get_or_none(email=data.email)
    if user is None:
        return  # silent — don't leak whether email exists

    raw_token = secrets.token_urlsafe(32)
    await VerificationToken.create(
        user=user,
        token_hash=_hash(raw_token),
        purpose=TokenPurpose.PASSWORD_RESET,
        expires_at=datetime.now(tz=timezone.utc) + timedelta(hours=1),
    )
    # TODO: send raw_token to user.email


@router.post("/password-reset/confirm", status_code=status.HTTP_204_NO_CONTENT)
async def confirm_password_reset(data: PasswordResetConfirm):
    token_hash = _hash(data.token)
    record = await VerificationToken.get_or_none(
        token_hash=token_hash, purpose=TokenPurpose.PASSWORD_RESET
    ).prefetch_related("user")

    if (
        record is None
        or record.used_at is not None
        or record.expires_at < datetime.now(tz=timezone.utc)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token"
        )

    record.used_at = datetime.now(tz=timezone.utc)
    await record.save()

    record.user.hashed_password = hash_password(data.new_password)
    await record.user.save()

    await RefreshToken.filter(user=record.user, revoked=False).update(revoked=True)


@router.post("/password/change", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    data: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
):
    ok, _ = (
        verify_password(data.current_password, current_user.hashed_password)
        if current_user.hashed_password
        else (False, None)
    )
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    current_user.hashed_password = hash_password(data.new_password)
    await current_user.save()

    await RefreshToken.filter(user=current_user, revoked=False).update(revoked=True)
