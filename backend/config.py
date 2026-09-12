"""
Centralized app settings, loaded from environment variables (.env file).
Every other module reads config values from here instead of calling
os.environ directly, so there's one source of truth.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    gemini_api_key: str = ""
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    database_url: str = "sqlite:///./peernotes.db"

    class Config:
        env_file = ".env"


settings = Settings()
