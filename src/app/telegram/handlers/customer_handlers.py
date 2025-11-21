import logging

from telethon import events
from telethon.client.telegramclient import TelegramClient

from src.app.config import settings
from src.app.services import conversation_service
from src.app.utils.formatting import format_new_customer_message

logger = logging.getLogger(__name__)


def register_customer_handlers(client: TelegramClient):

    @client.on(events.NewMessage(pattern="/start"))
    async def on_start(event):
        # 只处理私聊 /start
        if not event.is_private:
            return

        await event.respond(
            "嗨～这里是 SalmonCloud 客服机器人，你可以直接把问题发给我，我们会在这里回复你。"
        )

    @client.on(events.NewMessage(pattern="/stop"))
    async def on_stop(event):
        if not event.is_private:
            return

        try:
            conversation_service.handle_user_stop(event.chat_id)
            await event.respond("好的，我们不会再通过本机器人主动联系你。")
        except Exception:
            logger.exception("Failed to handle /stop")
            await event.respond("抱歉，处理你的请求时出现错误，请稍后再试。")

    @client.on(events.NewMessage)
    async def on_user_message(event):
        # 只处理私聊里的普通消息
        if not event.is_private:
            return

        # 命令交给其他 handler 或忽略
        if event.raw_text and event.raw_text.startswith("/"):
            return

        user = await event.get_sender()
        text = event.raw_text or ""

        try:
            conv, msg = conversation_service.handle_user_message(user, text, event)
        except Exception:
            logger.exception("Failed to handle user message")
            await event.respond("抱歉，系统暂时出了一点问题，请稍后再试。")
            return

        # 回一条确认给客户
        await event.respond("已收到，我们的同事会尽快在这里回复你 🙌")

        # 发到内部群
        internal_text = format_new_customer_message(conv, msg, user, event.chat_id)
        try:
            sent = await client.send_message(
                settings.internal_group_id,
                internal_text,
                reply_to=settings.internal_topic_id,  # 指定 topic
            )
        except Exception:
            logger.exception("Failed to send message to internal group")
            return

        # 回填内部群的 message_id
        try:
            conversation_service.bind_group_message(msg["id"], sent.id)
        except Exception:
            logger.exception("Failed to bind group message id")
