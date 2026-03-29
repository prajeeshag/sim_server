import pytest
from tortoise import Tortoise

TORTOISE_TEST_CONFIG = {
    "connections": {"default": "sqlite://:memory:"},
    "apps": {
        "models": {
            "models": [
                "sim_server.models.user",
                "sim_server.models.auth",
                "sim_server.models.rbac",
                "sim_server.models.audit",
            ],
            "default_connection": "default",
        }
    },
}


@pytest.fixture(autouse=True)
async def db():
    await Tortoise.init(config=TORTOISE_TEST_CONFIG)
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()
