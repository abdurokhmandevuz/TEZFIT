import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from config import settings
from database.session import init_db
from bot import bot, dp
from api.dashboard import router as api_router
from services.reminder_service import setup_reminders

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

polling_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global polling_task
    logger.info("Initializing database tables...")
    await init_db()

    logger.info("Starting APScheduler meal reminders...")
    setup_reminders(bot)

    logger.info("Starting Aiogram bot polling in background...")
    polling_task = asyncio.create_task(dp.start_polling(bot))

    yield

    logger.info("Shutting down bot polling...")
    if polling_task:
        polling_task.cancel()
        try:
            await polling_task
        except asyncio.CancelledError:
            pass
    await bot.session.close()
    logger.info("Shutdown complete.")

app = FastAPI(title="Kalorix API & Web App", lifespan=lifespan)

# Mount FastAPI REST API endpoints
app.include_router(api_router)

# Mount Static Files for Web App
app.mount("/web_app", StaticFiles(directory="web_app", html=True), name="web_app")

@app.get("/")
async def root():
    return {"message": "Kalorix Bot & Web App API service running!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=False)
