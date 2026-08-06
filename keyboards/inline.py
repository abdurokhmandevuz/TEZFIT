from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_meal_action_keyboard(temp_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Saqlash", callback_data=f"save_meal:{temp_id}"),
                InlineKeyboardButton(text="✏️ Tuzatish", callback_data=f"edit_meal:{temp_id}"),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"cancel_meal:{temp_id}")
            ]
        ]
    )

def get_edit_options_keyboard(temp_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⚖️ Vaznni o'zgartirish", callback_data=f"edit_weight:{temp_id}"),
                InlineKeyboardButton(text="📝 Nomni o'zgartirish", callback_data=f"edit_name:{temp_id}")
            ],
            [
                InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"back_meal:{temp_id}")
            ]
        ]
    )

def get_vip_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💎 VIP statusga o'tish", callback_data="buy_vip")
            ]
        ]
    )

def get_goals_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Formuladan qayta hisoblash", callback_data="recalc_goal"),
                InlineKeyboardButton(text="✏️ O'zgartirish", callback_data="custom_goal")
            ]
        ]
    )
