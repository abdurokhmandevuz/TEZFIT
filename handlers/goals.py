from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from database.session import AsyncSessionLocal
from services.user_service import UserService
from keyboards.inline import get_goals_keyboard
from states.user_states import CustomGoalState

router = Router()

@router.message(F.text == "🎯 Maqsadim")
async def show_goals(message: Message):
    async with AsyncSessionLocal() as session:
        user = await UserService.get_or_create_user(session, message.from_user.id)

    text = (
        f"🎯 **SIZNING KUNLIK MAQSADINGIZ**\n\n"
        f"📏 **Bo'y:** {user.height_cm or 170} sm\n"
        f"⚖️ **Vazn:** {user.weight_kg or 70} kg\n"
        f"👤 **Yosh:** {user.age or 25}\n"
        f"👫 **Jins:** {'Erkak 👨' if user.gender == 'male' else 'Ayol 👩'}\n\n"
        f"🔥 **Joriy kunlik kaloriya maqsadi:** **{user.daily_goal_kcal:.0f} kcal**\n\n"
        f"Maqsadni qayta hisoblash yoki o'zingiz kiritishingiz mumkin:"
    )
    await message.answer(text, reply_markup=get_goals_keyboard(), parse_mode="Markdown")

@router.callback_query(F.data == "recalc_goal")
async def process_recalc_goal(callback: CallbackQuery):
    async with AsyncSessionLocal() as session:
        user = await UserService.get_or_create_user(session, callback.from_user.id)
        w = user.weight_kg or 70.0
        h = user.height_cm or 170.0
        a = user.age or 25
        g = user.gender or "male"
        
        new_goal = UserService.calculate_mifflin_st_jeor(w, h, a, g)
        user.daily_goal_kcal = new_goal
        await session.commit()

    await callback.message.edit_text(
        f"✅ **Mifflin-St Jeor** formulasi bo'yicha qayta hisoblandi!\n\n"
        f"Yangi kunlik kaloriya norma maqsadingiz: **{new_goal:.0f} kcal**",
        parse_mode="Markdown"
    )
    await callback.answer("Qayta hisoblandi!")

@router.callback_query(F.data == "custom_goal")
async def process_custom_goal(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CustomGoalState.waiting_for_goal)
    await callback.message.answer(
        "✏️ Yangi kunlik kaloriya maqsadingizni son ko'rinishida kiriting (masalan: `2200`):",
        parse_mode="Markdown"
    )
    await callback.answer()

@router.message(CustomGoalState.waiting_for_goal)
async def process_custom_goal_value(message: Message, state: FSMContext):
    try:
        val = float(message.text.strip().replace(",", "."))
        if val < 800 or val > 10000:
            raise ValueError()
        
        async with AsyncSessionLocal() as session:
            user = await UserService.get_or_create_user(session, message.from_user.id)
            user.daily_goal_kcal = val
            await session.commit()

        await state.clear()
        await message.answer(f"✅ Kunlik kaloriya maqsadingiz **{val:.0f} kcal** qilib belgilandi!", parse_mode="Markdown")
    except ValueError:
        await message.answer("Iltimos, to'g'ri kaloriya miqdorini son ko'rinishida kiriting (masalan: `2200`):")
