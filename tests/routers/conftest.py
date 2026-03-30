from collections.abc import AsyncGenerator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pytest_postgresql import factories
from tortoise.contrib.fastapi import RegisterTortoise

from sim_server.deps import get_current_user
from sim_server.models.user import User
from sim_server.routers.users import router as users_router

postgresql_proc = factories.postgresql_proc()
postgresql = factories.postgresql("postgresql_proc")

TORTOISE_APPS = {
    "models": {
        "models": [
            "sim_server.models.user",
            "sim_server.models.audit",
        ],
        "default_connection": "default",
    }
}


@pytest.fixture()
async def app(postgresql):
    info = postgresql.info
    password = f":{info.password}" if info.password else ""
    db_url = f"asyncpg://{info.user}{password}@{info.host}:{info.port}/{info.dbname}"

    _app = FastAPI()
    _app.include_router(users_router)

    async with RegisterTortoise(
        _app,
        config={"connections": {"default": db_url}, "apps": TORTOISE_APPS},
        generate_schemas=True,
    ):
        yield _app


@pytest.fixture()
async def active_user(app) -> User:
    return await User.create(
        email="test@example.com",
        hashed_password="hashed",
        is_active=True,
        is_verified=True,
    )


@pytest.fixture()
async def client(app, active_user) -> AsyncGenerator[AsyncClient, None]:
    app.dependency_overrides[get_current_user] = lambda: active_user
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c
    app.dependency_overrides.clear()
