from aiogram import Router, F
from aiogram.types import Message
from database.session import AsyncSessionLocal
from services.user_service import UserService
from keyboards.inline import get_vip_keyboard
from config import settings

router = Router()

@router.message(F.text == "⚙️ Sozlamalar")
async def show_settings(message: Message):
    async with AsyncSessionLocal() as session:
        user = await UserService.get_or_create_user(session, message.from_user.id)

    status_str = "💎 VIP foydalanuvchi (Cheksiz)" if user.is_vip else f"Standard ({user.free_requests_today} / {settings.USER_FREE_DAILY_LIMIT} so'rov ishlatildi)"

    text = (
        f"⚙️ **SOZLAMALAR VA PROFIL**\n\n"
        f"👤 **Ism:** {user.name or 'Kiritilmagan'}\n"
        f"🆔 **Telegram ID:** `{user.telegram_id}`\n"
        f"Status: **{status_str}**\n\n"
        f"📐 **O'lchamlar:**\n"
        f"• Bo'y: {user.height_cm or 170} sm\n"
        f"• Vazn: {user.weight_kg or 70} kg\n"
        f"• Yosh: {user.age or 25}\n"
        f"• Jins: {'Erkak' if user.gender == 'male' else 'Ayol'}\n\n"
        f"Profilni yangilash uchun `/start` buyrug'ini bosing."
    )

    kb = None if user.is_vip else get_vip_keyboard()
    await message.answer(text, reply_markup=kb, parse_mode="Markdown")
