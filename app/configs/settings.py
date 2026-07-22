from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置，全部来自环境变量 / .env。"""

    app_name: str = "AI Short Drama Agent"
    app_env: str = "development"
    debug: bool = True
    cors_allowed_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
        ]
    )
    database_url: str = "sqlite:///./data/app.db"
    llm_provider: str = "deepseek"
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-v4-pro"
    deepseek_timeout_seconds: float = 120
    deepseek_max_tokens: int = 12000
    deepseek_thinking_enabled: bool = False

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
