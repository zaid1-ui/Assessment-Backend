"""Configuration layer using pydantic-settings - env based, no hardcoded secrets."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    secret_key: str = "dev-secret-please-override"
    database_url: str = "sqlite+aiosqlite:///./dev.db"
    log_level: str = "INFO"
    page_size_default: int = 20
    page_size_max: int = 100

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


class TestSettings(Settings):
    database_url: str = "sqlite+aiosqlite:///:memory:"
    secret_key: str = "test-secret"


@lru_cache
def get_settings() -> Settings:
    return Settings()
