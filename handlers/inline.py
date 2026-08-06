import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from database.session import AsyncSessionLocal
from services.user_service import UserService
from services.meal_service import MealService
from services.gamification_service import GamificationService
from pending import get_pending_meal, remove_pending_meal, PENDING_MEALS
from keyboards.inline import get_edit_options_keyboard, get_meal_action_keyboard
from states.user_states import EditMealState, CustomGoalState

logger = logging.getLogger(__name__)

router = Router()

def make_progress_bar(current: float, total: float, length: int = 10) -> str:
    if total <= 0:
        return "░" * length
    percent = min(current / total, 1.0)
    filled = int(round(percent * length))
    return "█" * filled + "░" * (length - filled)

@router.callback_query(F.data.startswith("save_meal:"))
async def process_save_meal(callback: CallbackQuery):
    temp_id = callback.data.split(":")[1]
    pending = get_pending_meal(temp_id)

    if not pending:
        await callback.answer("Ma'lumot topilmadi yoki allaqachon saqlangan.", show_alert=True)
        return

    async with AsyncSessionLocal() as session:
        user = await UserService.get_or_create_user(session, callback.from_user.id)
        
        # Save meal to database
        meal = await MealService.add_meal(
            session=session,
            user_id=user.id,
            food_name=pending["food_name"],
            weight_g=pending["weight_g"],
            calories=pending["calories"],
            protein_g=pending["protein_g"],
            fat_g=pending["fat_g"],
            carbs_g=pending["carbs_g"],
            photo_file_id=pending.get("photo_file_id")
        )

        # Update streak
        streak, _ = await GamificationService.update_user_streak(session, user)

        # Calculate today totals
        today_stats = await MealService.get_today_stats(session, user.id)

        # Check badges
        badges = await GamificationService.check_all_achievements(
            session, user, today_stats["total_calories"]
        )

    remove_pending_meal(temp_id)

    cal = today_stats["total_calories"]
    goal = user.daily_goal_kcal
    bar = make_progress_bar(cal, goal)
    pct = (cal / goal * 100) if goal > 0 else 0

    badge_str = ""
    if badges:
        badge_str = f"\n🎖 **Yangi yutuq(lar):** {', '.join(badges)}\n"

    success_text = (
        f"✅ **{meal.food_name}** ({meal.weight_g:.0f}g, {meal.calories:.0f} kcal) saqlandi!\n\n"
        f"📊 **Bugungi natija:**\n"
        f"🔥 Kaloriya: **{cal:.0f} / {goal:.0f} kcal** ({pct:.0f}%)\n"
        f"[{bar}]\n"
        f"🥩 Oqsil: {today_stats['total_protein']:.1f}g | 🧈 Yog: {today_stats['total_fat']:.1f}g | 🍚 Uglevod: {today_stats['total_carbs']:.1f}g\n"
        f"🔥 **Streak:** {streak} kun!"
        f"{badge_str}"
    )

    await callback.message.edit_text(success_text, parse_mode="Markdown")
    await callback.answer("✅ Saqlandi!")

@router.callback_query(F.data.startswith("edit_meal:"))
async def process_edit_meal(callback: CallbackQuery):
    temp_id = callback.data.split(":")[1]
    pending = get_pending_meal(temp_id)
    if not pending:
        await callback.answer("Ma'lumot topilmadi.", show_alert=True)
        return

    await callback.message.edit_text(
        f"✏️ **{pending['food_name']}** ma'lumotlarini o'zgartirish:\n\n"
        f"Hozirgi vazn: {pending['weight_g']:.0f}g | Hozirgi kaloriya: {pending['calories']:.0f} kcal",
        reply_markup=get_edit_options_keyboard(temp_id),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("back_meal:"))
async def process_back_meal(callback: CallbackQuery):
    temp_id = callback.data.split(":")[1]
    pending = get_pending_meal(temp_id)
    if not pending:
        await callback.answer("Ma'lumot topilmadi.", show_alert=True)
        return

    response_text = (
        f"🍽 **{pending['food_name']}** (taxminan {pending['weight_g']:.0f}g)\n"
        f"🔥 **Kaloriya:** {pending['calories']:.0f} kcal\n"
        f"🥩 **Oqsil:** {pending['protein_g']:.1f}g | 🧈 **Yog:** {pending['fat_g']:.1f}g | 🍚 **Uglevod:** {pending['carbs_g']:.1f}g\n"
    )
    await callback.message.edit_text(
        response_text,
        reply_markup=get_meal_action_keyboard(temp_id),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("edit_weight:"))
async def process_edit_weight(callback: CallbackQuery, state: FSMContext):
    temp_id = callback.data.split(":")[1]
    pending = get_pending_meal(temp_id)
    if not pending:
        await callback.answer("Ma'lumot topilmadi.", show_alert=True)
        return

    await state.update_data(temp_id=temp_id, edit_field="weight")
    await state.set_state(EditMealState.waiting_for_value)
    await callback.message.answer(
        f"⚖️ **{pending['food_name']}** uchun yangi og'irlikni (grammda) kiriting (masalan: `250`):",
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("edit_name:"))
async def process_edit_name(callback: CallbackQuery, state: FSMContext):
    temp_id = callback.data.split(":")[1]
    pending = get_pending_meal(temp_id)
    if not pending:
        await callback.answer("Ma'lumot topilmadi.", show_alert=True)
        return

    await state.update_data(temp_id=temp_id, edit_field="name")
    await state.set_state(EditMealState.waiting_for_value)
    await callback.message.answer(
        f"📝 Taom uchun yangi nomni kiriting (masalan: `Tovuqli palov`):",
        parse_mode="Markdown"
    )
    await callback.answer()

@router.message(EditMealState.waiting_for_value)
async def process_new_edit_value(message: Message, state: FSMContext):
    data = await state.get_data()
    temp_id = data.get("temp_id")
    edit_field = data.get("edit_field")

    pending = get_pending_meal(temp_id)
    if not pending:
        await message.answer("Tahrirlash seansi yakunlangan yoki topilmadi.")
        await state.clear()
        return

    if edit_field == "weight":
        try:
            new_weight = float(message.text.strip().replace(",", "."))
            if new_weight <= 0:
                raise ValueError()
            
            old_w = pending["weight_g"] or 1.0
            ratio = new_weight / old_w

            pending["weight_g"] = new_weight
            pending["calories"] = pending["calories"] * ratio
            pending["protein_g"] = pending["protein_g"] * ratio
            pending["fat_g"] = pending["fat_g"] * ratio
            pending["carbs_g"] = pending["carbs_g"] * ratio
            
            await message.answer(f"✅ Vazn {new_weight:.0f}g ga o'zgartirildi va qayta hisoblandi!")
        except ValueError:
            await message.answer("Iltimos, musbat son ko'rinishida grammni kiriting (masalan: `250`):")
            return
    elif edit_field == "name":
        pending["food_name"] = message.text.strip()
        await message.answer(f"✅ Taom nomi **{pending['food_name']}** ga o'zgartirildi!", parse_mode="Markdown")

    await state.clear()

    # Present updated meal confirmation
    response_text = (
        f"🍽 **{pending['food_name']}** (taxminan {pending['weight_g']:.0f}g)\n"
        f"🔥 **Kaloriya:** {pending['calories']:.0f} kcal\n"
        f"🥩 **Oqsil:** {pending['protein_g']:.1f}g | 🧈 **Yog:** {pending['fat_g']:.1f}g | 🍚 **Uglevod:** {pending['carbs_g']:.1f}g\n"
    )
    await message.answer(
        response_text,
        reply_markup=get_meal_action_keyboard(temp_id),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("cancel_meal:"))
async def process_cancel_meal(callback: CallbackQuery):
    temp_id = callback.data.split(":")[1]
    remove_pending_meal(temp_id)
    await callback.message.edit_text("❌ Ovqat kiritish bekor qilindi.")
    await callback.answer("Bekor qilindi.")

@router.callback_query(F.data == "buy_vip")
async def process_buy_vip(callback: CallbackQuery):
    async with AsyncSessionLocal() as session:
        user = await UserService.get_or_create_user(session, callback.from_user.id)
        user.is_vip = True
        await session.commit()
    
    await callback.message.answer(
        "🎉 **Tabriklaymiz! VIP Status faollashtirildi!**\n\n"
        "Endi sizda:\n"
        "• Cheksiz AI so'rovlar ✨\n"
        "• Yuqori aniqlikdagi Premium AI model 🤖\n"
        "• Ustuvor tahlil tezligi ⚡️",
        parse_mode="Markdown"
    )
    await callback.answer("VIP Faollashtirildi!")
