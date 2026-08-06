import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from config import settings

from handlers.start import router as start_router
from handlers.photo import router as photo_router
from handlers.text_meal import router as text_meal_router
from handlers.inline import router as inline_router
from handlers.stats import router as stats_router
from handlers.goals import router as goals_router
from handlers.leaderboard import router as leaderboard_router
from handlers.settings import router as settings_router

logger = logging.getLogger(__name__)

bot = Bot(token=settings.BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Register routers in priority order
dp.include_router(start_router)
dp.include_router(stats_router)
dp.include_router(goals_router)
dp.include_router(leaderboard_router)
dp.include_router(settings_router)
dp.include_router(inline_router)
dp.include_router(photo_router)
dp.include_router(text_meal_router)
