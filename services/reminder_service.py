import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from sqlalchemy import select
from database.session import AsyncSessionLocal
from database.models import User

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

async def send_meal_reminders(bot: Bot, meal_type: str):
    """Broadcast meal reminder to active users."""
    logger.info(f"Sending {meal_type} reminders...")
    messages = {
        "breakfast": "🌅 Xayrli tong! Nonushtangizni rasmga olib yoki matn ko'rinishida yuborishni unutmang ☕️",
        "lunch": "☀️ Tushlik vaqti bo'ldi! Bugungi tushlik ovqatingizni kiritib, kaloriyani hisoblang 🍲",
        "dinner": "🌙 Kechki ovqat vaqti! Kunlik kaloriya maqsadingizga erishdingizmi? Ovqatingizni kiriting 🥗"
    }

    text = messages.get(meal_type, "🍽 Ovqatingizni kiritishni unutmang!")

    async with AsyncSessionLocal() as session:
        stmt = select(User.telegram_id)
        res = await session.execute(stmt)
        user_ids = res.scalars().all()

        for telegram_id in user_ids:
            try:
                await bot.send_message(chat_id=telegram_id, text=text)
            except Exception as e:
                logger.warning(f"Could not send reminder to {telegram_id}: {e}")

async def check_vip_expirations(bot: Bot):
    """Notify VIP users about their active status and expiration warnings."""
    logger.info("Checking VIP expirations...")
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.is_vip == True)
        res = await session.execute(stmt)
        vip_users = res.scalars().all()

        for user in vip_users:
            try:
                msg = (
                    "👑 **TezFIT Premium Obunasi Eslatmasi!**\n\n"
                    "Sizning Premium obunangiz faol! ✨ Cheksiz AI taom skan qilish va barcha imkoniyatlardan foydalanmoqdasiz.\n\n"
                    "Obuna muddatini uzaytirish va statusni tekshirish uchun Web App Sozlamalariga kiring. 🚀"
                )
                await bot.send_message(chat_id=user.telegram_id, text=msg, parse_mode="Markdown")
            except Exception as e:
                logger.warning(f"Could not send VIP reminder to {user.telegram_id}: {e}")

def setup_reminders(bot: Bot):
    # Nonushta reminder at 08:00
    scheduler.add_job(
        send_meal_reminders,
        'cron',
        hour=8,
        minute=0,
        args=[bot, "breakfast"],
        id="reminder_breakfast",
        replace_existing=True
    )
    # Tushlik reminder at 13:00
    scheduler.add_job(
        send_meal_reminders,
        'cron',
        hour=13,
        minute=0,
        args=[bot, "lunch"],
        id="reminder_lunch",
        replace_existing=True
    )
    # Kechki ovqat reminder at 19:00
    scheduler.add_job(
        send_meal_reminders,
        'cron',
        hour=19,
        minute=0,
        args=[bot, "dinner"],
        id="reminder_dinner",
        replace_existing=True
    )
    # VIP expiration check at 10:00
    scheduler.add_job(
        check_vip_expirations,
        'cron',
        hour=10,
        minute=0,
        args=[bot],
        id="vip_expiration_check",
        replace_existing=True
    )
    
    if not scheduler.running:
        scheduler.start()
        logger.info("APScheduler reminder service started.")
