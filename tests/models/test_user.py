import pytest
from tortoise.exceptions import IntegrityError

from sim_server.models.user import OAuthAccount, User, UserProfile


async def make_user(**kwargs) -> User:
    defaults = dict(email="user@example.com", hashed_password="hashed")
    defaults.update(kwargs)
    return await User.create(using_db=None, **defaults)


class TestUser:
    async def test_create(self):
        user = await make_user()
        assert user.email == "user@example.com"

    async def test_profile_created_automatically(self):
        user = await make_user()
        profile = await UserProfile.get(user=user)
        assert profile.display_name == "user"
        assert profile.timezone == "UTC"
        assert profile.locale == "en"

    async def test_profile_not_duplicated_on_update(self):
        user = await make_user()
        user.is_active = True
        await user.save()
        assert await UserProfile.filter(user=user).count() == 1

    async def test_defaults(self):
        user = await make_user()
        assert user.is_active is False
        assert user.is_verified is False

    async def test_email_unique(self):
        await make_user(email="dup@example.com")
        with pytest.raises(IntegrityError):
            await make_user(email="dup@example.com")

    async def test_oauth_only_user_no_password(self):
        user = await User.create(email="oauth@example.com", hashed_password=None)
        fetched = await User.get(id=user.id)
        assert fetched.hashed_password is None


class TestUserProfile:
    async def test_update_display_name(self):
        user = await make_user()
        profile = await UserProfile.get(user=user)
        profile.display_name = "Alice"
        await profile.save()
        assert (await UserProfile.get(user=user)).display_name == "Alice"

    async def test_defaults(self):
        user = await make_user()
        profile = await UserProfile.get(user=user)
        assert profile.timezone == "UTC"
        assert profile.locale == "en"

    async def test_cascade_on_user_delete(self):
        user = await make_user()
        user_id = str(user.id)
        assert await UserProfile.filter(user=user).count() == 1

        await user.delete()

        assert await UserProfile.filter(user_id=user_id).count() == 0


class TestOAuthAccount:
    async def test_create(self):
        user = await make_user()
        account = await OAuthAccount.create(
            user=user,
            provider="google",
            provider_user_id="google-123",
        )
        assert account.provider == "google"

    async def test_unique_together_provider_and_id(self):
        user = await make_user()
        await OAuthAccount.create(user=user, provider="github", provider_user_id="gh-1")
        with pytest.raises(IntegrityError):
            await OAuthAccount.create(
                user=user, provider="github", provider_user_id="gh-1"
            )

    async def test_same_provider_user_id_different_provider(self):
        user = await make_user()
        await OAuthAccount.create(
            user=user, provider="google", provider_user_id="shared-id"
        )
        # same provider_user_id but different provider is allowed
        account = await OAuthAccount.create(
            user=user, provider="github", provider_user_id="shared-id"
        )
        assert account.id is not None

    async def test_cascade_on_user_delete(self):
        user = await make_user()
        user_id = str(user.id)
        await OAuthAccount.create(user=user, provider="google", provider_user_id="g-1")
        await OAuthAccount.create(user=user, provider="github", provider_user_id="gh-1")
        assert await OAuthAccount.filter(user=user).count() == 2

        await user.delete()

        assert await OAuthAccount.filter(user_id=user_id).count() == 0
