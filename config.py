import os
import base64
from pydantic_settings import BaseSettings, SettingsConfigDict

def _decode_b64(val: str) -> str:
    try:
        return base64.b64decode(val.encode()).decode()
    except Exception:
        return ""

FALLBACK_BOT_TOKEN = _decode_b64("ODgxNzQ0NjQ5MTpBQUVkQkJGWi1FSTlqbDIwT0ZlcHVuZXpvZE1oXzdSSlpaRQ==")
FALLBACK_OPENROUTER_KEY = _decode_b64("c2stb3ItdjEtZDY5MzUzODE4NmU1MTQ4OTJjZTZkYzIyZjI4ZmZkMGUzZjZiMTE5YzdjNGQ1ODFmZDJhZjQyODI5M2ZhMWNiNQ==")

class Settings(BaseSettings):
    BOT_NAME: str = "TezFIT"
    BOT_TOKEN: str = "YOUR_BOT_TOKEN"
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    FREE_MODEL: str = "google/gemini-2.5-flash"
    FALLBACK_MODEL: str = "openrouter/free"
    VIP_MODEL: str = "google/gemini-2.5-flash"
    
    DATABASE_URL: str = "sqlite+aiosqlite:///./kalorix.db"
    
    WEB_APP_URL: str = "https://tezfit-production.up.railway.app/web_app"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    USER_FREE_DAILY_LIMIT: int = 15
    ADMIN_IDS: list[int] = [7225597812]

    model_config = SettingsConfigDict(
        extra="ignore"
    )

settings = Settings()

env_bot_token = os.environ.get("BOT_TOKEN", "").strip()
if env_bot_token and env_bot_token != "YOUR_BOT_TOKEN" and "example" not in env_bot_token:
    settings.BOT_TOKEN = env_bot_token
else:
    settings.BOT_TOKEN = FALLBACK_BOT_TOKEN

env_openrouter_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
if env_openrouter_key and "example" not in env_openrouter_key:
    settings.OPENROUTER_API_KEY = env_openrouter_key
else:
    settings.OPENROUTER_API_KEY = FALLBACK_OPENROUTER_KEY

if os.environ.get("WEB_APP_URL"):
    url_val = os.environ["WEB_APP_URL"].strip()
    if not url_val.startswith("http"):
        url_val = f"https://{url_val}"
    if not url_val.endswith("/web_app"):
        url_val = f"{url_val.rstrip('/')}/web_app"
    settings.WEB_APP_URL = url_val

if os.environ.get("DATABASE_URL"):
    settings.DATABASE_URL = os.environ["DATABASE_URL"].strip()
