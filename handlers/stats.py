from aiogram import Router, F
from aiogram.types import Message
from database.session import AsyncSessionLocal
from services.user_service import UserService
from services.meal_service import MealService
from services.gamification_service import GamificationService

router = Router()

def make_progress_bar(current: float, total: float, length: int = 10) -> str:
    if total <= 0:
        return "░" * length
    percent = min(current / total, 1.0)
    filled = int(round(percent * length))
    return "█" * filled + "░" * (length - filled)

@router.message(F.text == "📊 Statistika")
async def show_stats(message: Message):
    async with AsyncSessionLocal() as session:
        user = await UserService.get_or_create_user(session, message.from_user.id)
        today_stats = await MealService.get_today_stats(session, user.id)
        weekly_stats = await MealService.get_weekly_stats(session, user.id)
        badges = await GamificationService.get_user_badges(session, user.id)

    cal = today_stats["total_calories"]
    goal = user.daily_goal_kcal
    bar = make_progress_bar(cal, goal)
    pct = (cal / goal * 100) if goal > 0 else 0

    weekly_total = sum([d["calories"] for d in weekly_stats])
    weekly_avg = weekly_total / 7.0

    badge_names = [b["name"] for b in badges] or ["Hali yutuqlar yo'q"]

    text = (
        f"📊 **KUNLIK STATISTIKA ({cal:.0f} / {goal:.0f} kcal)**\n"
        f"[{bar}] {pct:.0f}%\n\n"
        f"🥩 **Oqsil:** {today_stats['total_protein']:.1f}g\n"
        f"🧈 **Yog:** {today_stats['total_fat']:.1f}g\n"
        f"🍚 **Uglevod:** {today_stats['total_carbs']:.1f}g\n"
        f"🍽 **Yozilgan ovqatlar:** {today_stats['meal_count']} ta\n\n"
        f"📅 **HAFTALIK KO'RSATKICH:**\n"
        f"• 7 kunlik umumiy: {weekly_total:.0f} kcal\n"
        f"• Kunlik o'rtacha: {weekly_avg:.0f} kcal/kun\n\n"
        f"🔥 **Streak:** {user.streak_days} kun uzluksiz!\n"
        f"🎖 **Nishonlar:** {', '.join(badge_names)}"
    )

    await message.answer(text, parse_mode="Markdown")
