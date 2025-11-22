import logging
from telethon import TelegramClient
from telethon.tl import functions, types

from app.config import settings
from app.telegram.handlers.customer_handlers import register_customer_handlers
from app.telegram.handlers.staff_handlers import register_staff_handlers
from app.telegram.handlers.command_handlers import register_command_handlers

logger = logging.getLogger(__name__)


async def setup_bot_commands(client: TelegramClient):
    """
    用 Telethon 在代码里设置 / 菜单命令，相当于 BotFather 的 /setcommands
    """
    commands = [
        types.BotCommand(
            command="bm_stock_",                # 注意：只能小写字母/数字/下划线
            description="可交付独服库存查询",   # 描述可以是中文
        ),
        types.BotCommand(
            command="bw_price",
            description="独服带宽价格查询",
        ),
    ]

    await client(functions.bots.SetBotCommandsRequest(
        scope=types.BotCommandScopeDefault(),  # 默认作用域：所有聊天
        lang_code="",                          # 空字符串 = 所有语言
        commands=commands,
    ))
    logger.info("Bot commands have been set via MTProto.")


async def run_bot():
    client = TelegramClient(
        "salmoncloud_bot_session",
        settings.api_id,
        settings.api_hash,
    )

    await client.start(bot_token=settings.bot_token)

    # 启动后设置一次菜单命令
    await setup_bot_commands(client)

    register_command_handlers(client)
    register_customer_handlers(client)
    register_staff_handlers(client)

    logger.info("SalmonCloud bridge bot started.")
    await client.run_until_disconnected()
