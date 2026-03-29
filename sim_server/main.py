from contextlib import asynccontextmanager

from config import TORTOISE_ORM_CONFIG
from fastapi import FastAPI
from tortoise.contrib.fastapi import RegisterTortoise

from sim_server.routers.auth import router as auth_router
from sim_server.routers.users import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with RegisterTortoise(
        app,
        config=TORTOISE_ORM_CONFIG,
        generate_schemas=True,  # ← set False in prod, use aerich migrations
        add_exception_handlers=True,
    ):
        yield


app = FastAPI(title="JWT Auth API", lifespan=lifespan)
app.include_router(auth_router)
app.include_router(users_router)
