import pytest
from pytest_postgresql import factories
from tortoise import Tortoise

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


@pytest.fixture(autouse=True)
async def db(postgresql):
    info = postgresql.info
    db_url = (
        f"postgres://{info.user}:{info.password}@{info.host}:{info.port}/{info.dbname}"
    )

    await Tortoise.init(
        config={
            "connections": {"default": db_url},
            "apps": TORTOISE_APPS,
        }
    )
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()
