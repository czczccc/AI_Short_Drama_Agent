from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置，全部来自环境变量 / .env。"""

    app_name: str = "AI Short Drama Agent"
    app_env: str = "development"
    debug: bool = True
    database_url: str = "sqlite:///./app.db"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
