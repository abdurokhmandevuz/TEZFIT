from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from config import settings

def get_main_reply_keyboard() -> ReplyKeyboardMarkup:
    web_app_url = settings.WEB_APP_URL
    if not web_app_url.startswith("https://"):
        web_app_url = web_app_url.replace("http://", "https://")
        if not web_app_url.startswith("https://"):
            web_app_url = "https://" + web_app_url

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
