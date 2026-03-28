from contextlib import asynccontextmanager

from config import TORTOISE_ORM_CONFIG
from deps import get_current_user
from fastapi import Depends, FastAPI
from tortoise.contrib.fastapi import RegisterTortoise

from .routers.auth import router as auth_router


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


@app.get("/protected")
async def protected(current_user=Depends(get_current_user)):
    return {"message": f"Hello {current_user.username}!"}
