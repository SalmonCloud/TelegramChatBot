import logging
from telethon import TelegramClient

from src.app.config import settings
from src.app.telegram.handlers.customer_handlers import register_customer_handlers
from src.app.telegram.handlers.staff_handlers import register_staff_handlers

logger = logging.getLogger(__name__)


async def run_bot():
    client = TelegramClient(
        "salmoncloud_bot_session",
        settings.api_id,
        settings.api_hash,
    )

    await client.start(bot_token=settings.bot_token)

    register_customer_handlers(client)
    register_staff_handlers(client)

    logger.info("SalmonCloud bridge bot started.")
    await client.run_until_disconnected()
