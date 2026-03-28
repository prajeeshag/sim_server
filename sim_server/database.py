from abc import ABC, abstractmethod
from uuid import UUID, uuid4

from models.orm import UserORM
from models.schemas import UserCreate, UserInDB

from .security import hash_password


class UserRepository(ABC):
    @abstractmethod
    async def get_by_username(self, username: str) -> UserInDB | None: ...

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> UserInDB | None: ...

    @abstractmethod
    async def create(self, data: UserCreate) -> UserInDB: ...

    @abstractmethod
    async def update_password(self, username: str, new_hash: str) -> None: ...

    @abstractmethod
    async def exists(self, username: str) -> bool: ...


# ── Tortoise ORM Implementation (default) ──────────────────────────────────


class TortoiseUserRepository(UserRepository):
    @staticmethod
    def _to_schema(orm: UserORM) -> UserInDB:
        return UserInDB.model_validate(orm, from_attributes=True)

    async def get_by_username(self, username: str) -> UserInDB | None:
        orm = await UserORM.get_or_none(username=username)
        return self._to_schema(orm) if orm else None

    async def get_by_id(self, user_id: UUID) -> UserInDB | None:
        orm = await UserORM.get_or_none(id=user_id)
        return self._to_schema(orm) if orm else None

    async def create(self, data: UserCreate) -> UserInDB:
        orm = await UserORM.create(
            id=uuid4(),
            username=data.username,
            email=data.email,
            hashed_password=hash_password(data.password),
        )
        return self._to_schema(orm)

    async def update_password(self, username: str, new_hash: str) -> None:
        await UserORM.filter(username=username).update(hashed_password=new_hash)

    async def exists(self, username: str) -> bool:
        return await UserORM.filter(username=username).exists()


# ── In-Memory Implementation (testing only) ────────────────────────────────


class InMemoryUserRepository(UserRepository):
    def __init__(self):
        self._db: dict[str, UserInDB] = {}

    async def get_by_username(self, username: str) -> UserInDB | None:
        return self._db.get(username)

    async def get_by_id(self, user_id: UUID) -> UserInDB | None:
        return next((u for u in self._db.values() if u.id == user_id), None)

    async def create(self, data: UserCreate) -> UserInDB:
        from datetime import datetime, timezone

        user = UserInDB(
            id=uuid4(),
            username=data.username,
            email=data.email,
            hashed_password=hash_password(data.password),
            disabled=False,
            created_at=datetime.now(timezone.utc),
        )
        self._db[data.username] = user
        return user

    async def update_password(self, username: str, new_hash: str) -> None:
        if user := self._db.get(username):
            user.hashed_password = new_hash

    async def exists(self, username: str) -> bool:
        return username in self._db
