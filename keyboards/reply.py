import os
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from config import settings

def get_main_reply_keyboard() -> ReplyKeyboardMarkup:
    web_app_url = os.environ.get("WEB_APP_URL", settings.WEB_APP_URL)
    
    # Guarantee production Railway domain for Web App button
    if "loca.lt" in web_app_url or "localhost" in web_app_url or "127.0.0.1" in web_app_url or not web_app_url.startswith("https://"):
        web_app_url = "https://tezfit-production.up.railway.app/web_app"

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
