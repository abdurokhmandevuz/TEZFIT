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
    
    if not scheduler.running:
        scheduler.start()
        logger.info("APScheduler reminder service started.")
