import logging

from telethon import events
from telethon.client.telegramclient import TelegramClient

from src.app.config import settings
from src.app.services import conversation_service

logger = logging.getLogger(__name__)


def register_staff_handlers(client: TelegramClient):

    @client.on(events.NewMessage(chats=settings.internal_group_id))
    async def on_staff_message(event):
        """
        只处理在内部群里的“回复某条消息”的文本，
        把内容转发回对应客户。
        """
        # 必须是 reply 才认为是给客户的回复
        if not event.is_reply:
            return

        # 只处理来自指定 topic 的消息
        rt = event.message.reply_to
        # Telethon 里 forum topic 的 ID 可以通过 reply_to_top_id 拿到 :contentReference[oaicite:1]{index=1}
        if rt and getattr(rt, "reply_to_top_id", None) not in (
                None,
                settings.internal_topic_id,
        ):
            return

        # 预留命令位（以后可以做 /close 等）
        if event.raw_text and event.raw_text.startswith("/"):
            return

        reply_to = await event.get_reply_message()
        text = event.raw_text or ""
        staff = await event.get_sender()

        try:
            target_chat_id = conversation_service.handle_staff_reply(
                reply_to_message_id=reply_to.id,
                staff=staff,
                text=text,
                event=event,
            )
        except Exception:
            logger.exception("Failed to handle staff reply")
            await event.reply("处理回复时出现错误。")
            return

        if not target_chat_id:
            await event.reply("找不到对应的客户会话，可能是历史消息或没有建立映射。")
            return

        # 通过 bot 把消息转发给客户
        try:
            await client.send_message(target_chat_id, f"👩‍💻 SalmonCloud 团队：\n{text}")
        except Exception:
            logger.exception("Failed to send message to customer")
            await event.reply("向客户发送消息失败（可能对方已拉黑 bot）。")
