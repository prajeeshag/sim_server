from enum import Enum

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvChoices(str, Enum):
    prod = "prod"
    dev = "dev"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    env: EnvChoices = Field(default=EnvChoices.prod, alias="ENV")
    secret_key: str = Field(default="", alias="SECRET_KEY")
    db_url: str = Field(default="", alias="DB_URL")
    access_token_expire_minutes: int = Field(
        default=15, alias="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    refresh_token_expire_days: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")

    @model_validator(mode="after")
    def resolve_prod_settings(self) -> "Settings":
        if self.env != EnvChoices.prod:
            return self
        if not self.secret_key:
            raise ValueError("SECRET_KEY must be set in production")
        if self.db_url == "":
            raise ValueError("DB_URL should be set in production")
        return self


settings = Settings()
