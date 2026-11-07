from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ai_provider: str = "groq"
    ai_api_key: str = ""
    ai_model: str = "openai/gpt-oss-20b"
    ai_base_url: str = "https://api.groq.com/openai/v1"
    frontend_origin: str = "http://localhost:5173"
    max_upload_mb: int = 20

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
