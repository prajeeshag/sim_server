from datetime import datetime, timedelta, timezone

import pytest
from tortoise.exceptions import IntegrityError

from sim_server.models.user import RefreshToken, TokenPurpose, User, VerificationToken


async def make_user(email="auth@example.com") -> User:
    return await User.create(email=email)


def future_dt(hours: int = 1) -> datetime:
    return datetime.now(tz=timezone.utc) + timedelta(hours=hours)


class TestRefreshToken:
    async def test_create(self):
        user = await make_user()
        token = await RefreshToken.create(
            user=user,
            token_hash="abc123hash",
            expires_at=future_dt(24),
        )
        assert token.revoked is False

    async def test_token_hash_unique(self):
        user = await make_user()
        await RefreshToken.create(user=user, token_hash="unique-hash", expires_at=future_dt())
        with pytest.raises(IntegrityError):
            await RefreshToken.create(user=user, token_hash="unique-hash", expires_at=future_dt())

    async def test_cascade_on_user_delete(self):
        user = await make_user()
        user_id = str(user.id)
        await RefreshToken.create(user=user, token_hash="hash-a", expires_at=future_dt())
        await RefreshToken.create(user=user, token_hash="hash-b", expires_at=future_dt())
        assert await RefreshToken.filter(user=user).count() == 2

        await user.delete()

        assert await RefreshToken.filter(user_id=user_id).count() == 0


class TestVerificationToken:
    async def test_create_email_verify(self):
        user = await make_user()
        token = await VerificationToken.create(
            user=user,
            token_hash="verify-hash",
            purpose=TokenPurpose.EMAIL_VERIFY,
            expires_at=future_dt(),
        )
        assert token.purpose == TokenPurpose.EMAIL_VERIFY
        assert token.used_at is None

    async def test_create_password_reset(self):
        user = await make_user()
        token = await VerificationToken.create(
            user=user,
            token_hash="reset-hash",
            purpose=TokenPurpose.PASSWORD_RESET,
            expires_at=future_dt(),
        )
        assert token.purpose == TokenPurpose.PASSWORD_RESET

    async def test_token_hash_unique(self):
        user = await make_user()
        await VerificationToken.create(
            user=user,
            token_hash="dup-hash",
            purpose=TokenPurpose.EMAIL_VERIFY,
            expires_at=future_dt(),
        )
        with pytest.raises(IntegrityError):
            await VerificationToken.create(
                user=user,
                token_hash="dup-hash",
                purpose=TokenPurpose.PASSWORD_RESET,
                expires_at=future_dt(),
            )

    async def test_cascade_on_user_delete(self):
        user = await make_user()
        user_id = str(user.id)
        await VerificationToken.create(
            user=user,
            token_hash="v-hash",
            purpose=TokenPurpose.EMAIL_VERIFY,
            expires_at=future_dt(),
        )
        assert await VerificationToken.filter(user=user).count() == 1

        await user.delete()

        assert await VerificationToken.filter(user_id=user_id).count() == 0
