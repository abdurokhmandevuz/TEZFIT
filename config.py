import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    BOT_TOKEN: str = "YOUR_BOT_TOKEN"
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    FREE_MODEL: str = "nvidia/nemotron-3-ultra-550b-a55b:free"
    FALLBACK_MODEL: str = "openrouter/free"
    VIP_MODEL: str = "google/gemini-2.5-pro"
    
    DATABASE_URL: str = "sqlite+aiosqlite:///./kalorix.db"
    
    WEB_APP_URL: str = "http://localhost:8000/web_app"
    HOST: str = "0.0.0.0"
    PORT: int = int(os.environ.get("PORT", "8000"))
    
    USER_FREE_DAILY_LIMIT: int = 10

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
