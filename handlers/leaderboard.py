from aiogram import Router, F
from aiogram.types import Message
from database.session import AsyncSessionLocal
from services.gamification_service import GamificationService

router = Router()

@router.message(F.text == "🏆 Reyting")
async def show_leaderboard(message: Message):
    async with AsyncSessionLocal() as session:
        board = await GamificationService.get_leaderboard(session, limit=10)

    medals = ["🥇", "🥈", "🥉"]
    lines = ["🏆 **ENG YUQORI STREAK REYTINGI**\n"]

    if not board:
        lines.append("Hali hech kim streak o'rnatmadi. Birinchi bo'ling!")
    else:
        for item in board:
            rank = item["rank"]
            medal = medals[rank - 1] if rank <= 3 else f"#{rank}"
            vip_tag = "💎 " if item["is_vip"] else ""
            lines.append(f"{medal} {vip_tag}**{item['name']}** — 🔥 {item['streak']} kun")

    lines.append("\n💡 *Streakni oshirish uchun har kuni ovqatlaringizni kiritib boring!*")
    await message.answer("\n".join(lines), parse_mode="Markdown")
