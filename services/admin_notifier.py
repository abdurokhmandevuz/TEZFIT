import os
import asyncio
import logging
from datetime import datetime
from config import settings

logger = logging.getLogger(__name__)

ADMIN_ID = settings.ADMIN_IDS[0] if settings.ADMIN_IDS else 7225597812

class TelegramAdminLogHandler(logging.Handler):
    """Custom logging handler that forwards ERROR and CRITICAL logs directly to Admin Telegram."""
    def __init__(self, bot):
        super().__init__(level=logging.ERROR)
        self.bot = bot
        self.last_sent = 0
        self.send_cooldown = 3.0  # Seconds between log messages to prevent spam

    def emit(self, record):
        if not self.bot:
            return
        
        # Don't send telegram API errors to avoid infinite loops
        if "telegram" in record.name.lower() or "aiogram" in record.name.lower():
            if "Conflict" in record.getMessage() or "BotBlocked" in record.getMessage():
                return

        now = datetime.utcnow().timestamp()
        if now - self.last_sent < self.send_cooldown:
            return
        self.last_sent = now

        try:
            formatted_msg = self.format(record)
            short_msg = formatted_msg[:1200] if len(formatted_msg) > 1200 else formatted_msg
            
            text = (
                f"🚨 **SERVER ERROR LOG / XATOLIK!**\n\n"
                f"⏰ **Vaqt:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`\n"
                f"📍 **Logger:** `{record.name}`\n"
                f"⚠️ **Level:** `{record.levelname}`\n\n"
                f"```text\n{short_msg}\n```"
            )
            
            # Fire-and-forget task loop
            try:
                loop = asyncio.get_running_loop()
                if loop.is_running():
                    loop.create_task(self._send_telegram(text))
            except RuntimeError:
                pass
        except Exception:
            pass

    async def _send_telegram(self, text: str):
        try:
            await self.bot.send_message(chat_id=ADMIN_ID, text=text, parse_mode="Markdown")
        except Exception as e:
            logger.warning(f"Could not send log notification to admin telegram: {e}")


async def notify_server_startup(bot):
    """Send server startup / redeploy notification to admin."""
    commit_sha = os.environ.get("RAILWAY_GIT_COMMIT_SHA", "HEAD")[:7]
    deploy_id = os.environ.get("RAILWAY_DEPLOYMENT_ID", "local")[:12]
    service_name = os.environ.get("RAILWAY_SERVICE_NAME", "TezFIT Production")
    
    text = (
        f"🟢 **TEZFIT SERVER REDEPLOYED / ISHGA TUSHDI!**\n\n"
        f"⏰ **Vaqt:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`\n"
        f"📦 **Servis:** `{service_name}`\n"
        f"📌 **Commit:** `{commit_sha}`\n"
        f"🚀 **Railway Deploy ID:** `{deploy_id}`\n\n"
        f"✅ **Holat:** FastAPI API, Bot Polling va Barcha Modullar Faol!"
    )
    try:
        await bot.send_message(chat_id=ADMIN_ID, text=text, parse_mode="Markdown")
    except Exception as e:
        logger.warning(f"Failed to send startup notification: {e}")


async def notify_server_shutdown(bot):
    """Send server shutdown / restart notification to admin."""
    text = (
        f"🔴 **TEZFIT SERVER SHUTDOWN / TO'XTATILDI!**\n\n"
        f"⏰ **Vaqt:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`\n"
        f"⚠️ **Holat:** Konteyner to'xtatildi yoki yangilanish (redeploy) bo'lmoqda."
    )
    try:
        await bot.send_message(chat_id=ADMIN_ID, text=text, parse_mode="Markdown")
    except Exception as e:
        logger.warning(f"Failed to send shutdown notification: {e}")
