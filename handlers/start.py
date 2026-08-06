from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from database.session import AsyncSessionLocal
from services.user_service import UserService
from keyboards.reply import get_main_reply_keyboard

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    async with AsyncSessionLocal() as session:
        user = await UserService.get_or_create_user(
            session=session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            name=message.from_user.full_name
        )

    welcome_text = (
        f"Assalomu alaykum, {message.from_user.first_name}! 🥗\n\n"
        f"**Kalorix** — Sizning intellektual kaloriya va taom tahlilchi yordamchingiz.\n\n"
        f"📸 **Shunchaki ovqatingiz rasmini yuboring** yoki matn ko'rinishida yozing (masalan: `200g osh`).\n\n"
        f"AI soniyalar ichida uning kaloriyasi va BJU (oqsil/yog'/uglevod) miqdorini aniqlab beradi! 🚀"
    )
    await message.answer(welcome_text, reply_markup=get_main_reply_keyboard(), parse_mode="Markdown")
