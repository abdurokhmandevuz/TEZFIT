import os
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, ReplyKeyboardRemove, FSInputFile
from aiogram.fsm.context import FSMContext

from config import settings
from database.session import AsyncSessionLocal
from services.user_service import UserService

router = Router()

# Path to welcome banner image
WELCOME_BANNER = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web_app", "assets", "tezfit_welcome.jpg")

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    async with AsyncSessionLocal() as session:
        user = await UserService.get_or_create_user(
            session=session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            name=message.from_user.full_name,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name
        )

    web_app_url = os.environ.get("WEB_APP_URL", settings.WEB_APP_URL)
    if "loca.lt" in web_app_url or "localhost" in web_app_url or not web_app_url.startswith("https://"):
        web_app_url = "https://tezfit-production.up.railway.app/web_app"

    target_url = f"{web_app_url}?v=2.9.7"

    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚀 TezFIT Web App-ni Ochish",
                    web_app=WebAppInfo(url=target_url)
                )
            ]
        ]
    )

    welcome_text = (
        f"👋 *Assalomu alaykum, {message.from_user.first_name}!*\n\n"
        f"🍏 *TezFIT* — Sizning shaxsiy AI ovqatlanish yordamchingiz!\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"✨ *Imkoniyatlar:*\n\n"
        f"📸  Taom rasmini yuboring — AI kaloriyasini aniqlaydi\n"
        f"✍️  Taom nomini yozing — tarkibi hisoblanadi\n"
        f"📊  Kunlik kaloriya va BJU kuzatuvi\n"
        f"💧  Suv ichish hisobi\n"
        f"🏋️  Mashqlar va yoqilgan kaloriya\n"
        f"🎯  Maqsadga erishish statistikasi\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"👇 *Boshlash uchun quyidagi tugmani bosing:*"
    )

    await message.answer("⏳", reply_markup=ReplyKeyboardRemove())

    try:
        photo = FSInputFile(WELCOME_BANNER)
        await message.answer_photo(
            photo=photo,
            caption=welcome_text,
            reply_markup=inline_kb,
            parse_mode="Markdown"
        )
    except Exception:
        await message.answer(welcome_text, reply_markup=inline_kb, parse_mode="Markdown")

