from httpx import AsyncClient

from sim_server.models.user import OAuthAccount, User, UserProfile


class TestGetMe:
    async def test_returns_user(self, client: AsyncClient, active_user: User):
        resp = await client.get("/users/me")
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == active_user.email
        assert "hashed_password" not in data

    async def test_includes_profile(self, client: AsyncClient):
        resp = await client.get("/users/me")
        assert "profile" in resp.json()
        assert resp.json()["profile"]["display_name"] == "test"

    async def test_unauthenticated(self, app, active_user: User):
        from httpx import ASGITransport, AsyncClient

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as c:
            resp = await c.get("/users/me")
        assert resp.status_code == 401


class TestGetMyProfile:
    async def test_returns_profile(self, client: AsyncClient, active_user: User):
        resp = await client.get("/users/me/profile")
        assert resp.status_code == 200
        data = resp.json()
        assert data["display_name"] == "test"
        assert data["timezone"] == "UTC"
        assert data["locale"] == "en"


class TestUpdateMyProfile:
    async def test_update_display_name(self, client: AsyncClient):
        resp = await client.patch("/users/me/profile", json={"display_name": "Alice"})
        assert resp.status_code == 200
        assert resp.json()["display_name"] == "Alice"

    async def test_partial_update(self, client: AsyncClient):
        await client.patch("/users/me/profile", json={"timezone": "Europe/London"})
        resp = await client.get("/users/me/profile")
        data = resp.json()
        assert data["timezone"] == "Europe/London"
        assert data["locale"] == "en"  # unchanged

    async def test_update_multiple_fields(self, client: AsyncClient):
        resp = await client.patch(
            "/users/me/profile",
            json={"display_name": "Bob", "bio": "Hello", "locale": "fr"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["display_name"] == "Bob"
        assert data["bio"] == "Hello"
        assert data["locale"] == "fr"

    async def test_unknown_fields_ignored(self, client: AsyncClient):
        resp = await client.patch("/users/me/profile", json={"nonexistent": "value"})
        assert resp.status_code == 200


class TestGetMyOAuthAccounts:
    async def test_empty(self, client: AsyncClient):
        resp = await client.get("/users/me/oauth-accounts")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_returns_linked_accounts(
        self, client: AsyncClient, active_user: User
    ):
        await OAuthAccount.create(
            user=active_user, provider="google", provider_user_id="g-123"
        )
        await OAuthAccount.create(
            user=active_user, provider="github", provider_user_id="gh-456"
        )
        resp = await client.get("/users/me/oauth-accounts")
        assert resp.status_code == 200
        providers = {a["provider"] for a in resp.json()}
        assert providers == {"google", "github"}

    async def test_does_not_expose_access_token(
        self, client: AsyncClient, active_user: User
    ):
        await OAuthAccount.create(
            user=active_user,
            provider="google",
            provider_user_id="g-1",
            access_token="secret-token",
        )
        resp = await client.get("/users/me/oauth-accounts")
        assert "access_token" not in resp.json()[0]


class TestDeleteMe:
    async def test_deletes_user(self, client: AsyncClient, active_user: User):
        resp = await client.delete("/users/me")
        assert resp.status_code == 204
        assert not await User.filter(id=active_user.id).exists()

    async def test_cascades_profile(self, client: AsyncClient, active_user: User):
        user_id = str(active_user.id)
        await client.delete("/users/me")
        assert not await UserProfile.filter(user_id=user_id).exists()
