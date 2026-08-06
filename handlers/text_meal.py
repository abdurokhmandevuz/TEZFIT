import re
import logging
from aiogram import Router, F
from aiogram.types import Message
from database.session import AsyncSessionLocal
from services.user_service import UserService
from services.ai_service import AIService
from pending import create_pending_meal
from keyboards.inline import get_meal_action_keyboard, get_vip_keyboard

logger = logging.getLogger(__name__)

router = Router()

# List of reply buttons to ignore in text meal handler
REPLY_BUTTONS = [
    "📊 Statistika",
    "🎯 Maqsadim",
    "🏆 Reyting",
    "⚙️ Sozlamalar",
    "📱 Web App",
    "Erkak 👨",
    "Ayol 👩"
]

FOOD_KEYWORDS = [
    "osh", "somsa", "shashlik", "non", "olma", "go'sht", "gosht", "tovuq", "tuxum", 
    "salat", "shurva", "shorva", "pitsa", "pizza", "burger", "qahva", "kofe", "choy", 
    "guruch", "manti", "lag'mon", "lagmon", "kabob", "shirinlik", "tort", "shokolad", 
    "sut", "qatiq", "tvorog", "pishloq", "banan", "guruch", "makaron", "kartoshka", "shurva",
    "gram", "gramm", "gr", "kg", "ta", "dona", "piyola", "kosa", "liti", "ml"
]

def is_food_description(text: str) -> bool:
    text_lower = text.lower().strip()
    # Check if text contains numbers along with letters, or food keywords
    has_digits = bool(re.search(r'\d+', text_lower))
    has_food_kw = any(kw in text_lower for kw in FOOD_KEYWORDS)
    
    # If it has digit + unit (e.g. 200g, 1ta) or food keyword, treat as food
    if (has_digits and len(text_lower) >= 3) or has_food_kw:
        return True
    return False

@router.message(F.text)
async def handle_food_text(message: Message):
    text = message.text.strip()

    # Skip menu buttons and commands
    if text in REPLY_BUTTONS or text.startswith("/"):
        return

    if not is_food_description(text):
        await message.answer(
            "💡 Ovqat kaloriyasini hisoblash uchun:\n"
            "• Ovqatingiz **rasmini yuboring** 📸\n"
            "• Yoki miqdori va nomini matn ko'rinishida yozing (masalan: `200g osh`, `2 ta tuxum`, `1 ta olma`) 📝",
            parse_mode="Markdown"
        )
        return

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
        parsed_data = await AIService.analyze_food_text(text, is_vip=user.is_vip)
        
        temp_id = create_pending_meal(
            user_id=user.id,
            parsed_data=parsed_data
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
        logger.error(f"Text analysis error: {e}", exc_info=True)
        await msg.edit_text("Kechirasiz, ovqatni tahlil qilib bo'lmadi. Iltimos, qaytadan aniqroq yozib ko'ring 🔄")
