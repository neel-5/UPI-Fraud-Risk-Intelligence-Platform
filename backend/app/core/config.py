from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "UPI Fraud Risk Intelligence API"
    app_env: str = "development"
    database_path: str = "storage/upi_fraud.db"
    frontend_origin: str = "http://localhost:5173"
    seed_on_startup: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def database_file(self) -> Path:
        return Path(self.database_path)


@lru_cache
def get_settings() -> Settings:
    return Settings()
