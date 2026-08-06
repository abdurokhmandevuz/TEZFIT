import io
import logging
from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from database.session import AsyncSessionLocal
from services.user_service import UserService
from services.ai_service import AIService
from pending import create_pending_meal
from keyboards.inline import get_meal_action_keyboard, get_vip_keyboard

logger = logging.getLogger(__name__)

router = Router()

@router.message(F.photo)
async def handle_food_photo(message: Message, bot: Bot, state: FSMContext):
    await state.clear()
    async with AsyncSessionLocal() as session:
        user = await UserService.get_or_create_user(session, message.from_user.id)
        allowed, remaining = await UserService.check_and_increment_limit(session, user)

    if not allowed:
        await message.answer(
            "⚠️ Bugungi bepul so'rovlar me'yoringiz tugadi!\n\n"
            "Cheksiz so'rovlar va kuchliroq AI modellar uchun VIP statusga o'ting 💎",
            reply_markup=get_vip_keyboard()
        )
        return

    msg = await message.answer("🔍 Tahlil qilinmoqda...")

    try:
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
        photo_bytes_io = await bot.download_file(file_info.file_path)
        image_bytes = photo_bytes_io.read()

        parsed_data = await AIService.analyze_food_image(image_bytes, is_vip=user.is_vip)
        
        temp_id = create_pending_meal(
            user_id=user.id,
            parsed_data=parsed_data,
            photo_file_id=photo.file_id
        )
        
        items = parsed_data.get("items", [])
        food_name = parsed_data.get("food_name", ", ".join([i.get("name", "Ovqat") for i in items]) or "Noma'lum ovqat")
        
        total_w = sum([float(i.get("weight_g", 0)) for i in items]) or 100.0
        total_cal = parsed_data.get("total_calories") or sum([float(i.get("calories", 0)) for i in items])
        total_p = sum([float(i.get("protein_g", 0)) for i in items])
        total_f = sum([float(i.get("fat_g", 0)) for i in items])
        total_c = sum([float(i.get("carbs_g", 0)) for i in items])

        response_text = (
            f"🍽 **{food_name}** (taxminan {total_w:.0f}g)\n"
            f"🔥 **Kaloriya:** {total_cal:.0f} kcal\n"
            f"🥩 **Oqsil:** {total_p:.1f}g | 🧈 **Yog:** {total_f:.1f}g | 🍚 **Uglevod:** {total_c:.1f}g\n"
        )
        if not user.is_vip and remaining >= 0:
            response_text += f"\nℹ️ *Bugungi qolgan bepul so'rovlar:* {remaining} ta"

        await msg.edit_text(
            response_text,
            reply_markup=get_meal_action_keyboard(temp_id),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Photo analysis error: {e}", exc_info=True)
        await msg.edit_text("Kechirasiz, ovqatni tahlil qilib bo'lmadi. Iltimos, boshqa rasm bilan qaytadan urinib ko'ring 🔄")
