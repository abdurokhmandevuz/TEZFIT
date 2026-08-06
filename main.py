import os
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
startup_error = None

async def run_bot_polling_with_retry():
    """Keep polling resilient against temporary Telegram network drops or container restarts."""
    while True:
        try:
            logger.info("Starting Aiogram bot polling in background...")
            await dp.start_polling(bot)
        except asyncio.CancelledError:
            logger.info("Bot polling loop cancelled.")
            break
        except Exception as e:
            logger.error(f"Polling disconnected: {e}. Retrying in 3 seconds...")
            await asyncio.sleep(3)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global polling_task, startup_error
    try:
        logger.info("Initializing database tables...")
        await init_db()
    except Exception as e:
        logger.error(f"DB Init Error: {e}", exc_info=True)
        startup_error = str(e)

    try:
        logger.info("Starting APScheduler meal reminders...")
        setup_reminders(bot)
    except Exception as e:
        logger.error(f"Reminder Setup Error: {e}", exc_info=True)

    try:
        polling_task = asyncio.create_task(run_bot_polling_with_retry())
    except Exception as e:
        logger.error(f"Bot Polling Task Error: {e}", exc_info=True)

    yield

    logger.info("Shutting down bot polling...")
    if polling_task:
        polling_task.cancel()
        try:
            await polling_task
        except asyncio.CancelledError:
            pass
    try:
        await bot.session.close()
    except Exception:
        pass
    logger.info("Shutdown complete.")

app = FastAPI(title="Kalorix API & Web App", lifespan=lifespan)

# Mount FastAPI REST API endpoints
app.include_router(api_router)

# Mount Static Files for Web App
if os.path.exists("web_app"):
    app.mount("/web_app", StaticFiles(directory="web_app", html=True), name="web_app")

@app.get("/")
async def root():
    status = "OK" if not startup_error else f"Warning: {startup_error}"
    return {"status": status, "message": "Kalorix Bot & Web App API service running!"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Starting server on host 0.0.0.0 and port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
