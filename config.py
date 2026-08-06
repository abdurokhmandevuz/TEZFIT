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
    
    WEB_APP_URL: str = "https://tezfit-production.up.railway.app/web_app"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    USER_FREE_DAILY_LIMIT: int = 10

    model_config = SettingsConfigDict(
        extra="ignore"
    )

settings = Settings()

# Force os.environ to override any settings defaults in Railway/production
if os.environ.get("BOT_TOKEN"):
    settings.BOT_TOKEN = os.environ["BOT_TOKEN"].strip()

if os.environ.get("OPENROUTER_API_KEY"):
    settings.OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"].strip()

if os.environ.get("WEB_APP_URL"):
    settings.WEB_APP_URL = os.environ["WEB_APP_URL"].strip()

if os.environ.get("DATABASE_URL"):
    settings.DATABASE_URL = os.environ["DATABASE_URL"].strip()
