from contextlib import asynccontextmanager

from config import EnvChoices, settings
from fastapi import FastAPI
from tortoise.contrib.fastapi import RegisterTortoise

from sim_server.routers.admin import router as admin_router
from sim_server.routers.auth import router as auth_router
from sim_server.routers.users import router as users_router

TORTOISE_ORM_CONFIG = {
    "connections": {"default": settings.db_url},
    "apps": {
        "models": {
            "models": [
                "sim_server.models.user",
                "sim_server.models.audit",
            ],
            "default_connection": "default",
        },
    },
}

generate_schemas = True if settings.env == EnvChoices.dev else False


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with RegisterTortoise(
        app,
        config=TORTOISE_ORM_CONFIG,
        generate_schemas=generate_schemas,
        add_exception_handlers=True,
    ):
        yield


app = FastAPI(title="Simrun Server", lifespan=lifespan)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(admin_router)
