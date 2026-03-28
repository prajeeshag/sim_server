from enum import Enum

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings

TEST_DB = "sqlite://:memory:"


class EnvChoices(str, Enum):
    prod = "prod"
    dev = "dev"
    test = "test"


class Settings(BaseSettings):
    env: EnvChoices = EnvChoices.prod
    secret_key: str = Field(default="xxx")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # Tortoise ORM
    db_url: str = TEST_DB
    # Production examples:
    # db_url: str = "postgres://user:pass@localhost:5432/mydb"
    # db_url: str = "mysql://user:pass@localhost:3306/mydb"

    class Config:
        env_file = ".env"

    @model_validator(mode="after")
    def resolve_prod_settings(self) -> "Settings":
        if self.env != EnvChoices.prod:
            return self
        if not self.secret_key:
            raise ValueError("SECRET_KEY must be set in production")
        if self.db_url == TEST_DB:
            raise ValueError("DB_URL should be set in production")
        return self


settings = Settings()

TORTOISE_ORM_CONFIG = {
    "connections": {"default": settings.db_url},
    "apps": {
        "models": {
            "models": ["models.orm", "aerich.models"],
            "default_connection": "default",
        }
    },
}
