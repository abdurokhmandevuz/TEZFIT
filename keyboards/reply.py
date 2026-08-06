import os
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from config import settings

def get_main_reply_keyboard() -> ReplyKeyboardMarkup:
    web_app_url = os.environ.get("WEB_APP_URL", settings.WEB_APP_URL)
    
    # Fallback to railway domain if localhost or localtunnel in production
    if "localhost" in web_app_url or "loca.lt" in web_app_url or not web_app_url.startswith("https://"):
        if os.environ.get("RAILWAY_STATIC_URL"):
            web_app_url = f"https://{os.environ.get('RAILWAY_STATIC_URL')}/web_app"
        elif not web_app_url.startswith("https://"):
            web_app_url = web_app_url.replace("http://", "https://")

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📊 Statistika"),
                KeyboardButton(text="🎯 Maqsadim")
            ],
            [
                KeyboardButton(text="🏆 Reyting"),
                KeyboardButton(text="⚙️ Sozlamalar")
            ],
            [
                KeyboardButton(text="📱 Web App", web_app=WebAppInfo(url=web_app_url))
            ]
        ],
        resize_keyboard=True,
        persistent=True
    )
    return kb

def get_gender_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Erkak 👨"), KeyboardButton(text="Ayol 👩")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
