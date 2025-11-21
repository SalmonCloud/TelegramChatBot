import logging
from typing import Tuple, Optional

from telethon.tl.types import User

from app.db import repositories as repo

logger = logging.getLogger(__name__)


def handle_user_message(user: User, text: str, event) -> Tuple[dict, dict]:
    """
    处理来自用户的私聊消息：
    - 确保 telegram_users 里有用户
    - 找到/创建 open 会话
    - 插入一条 from_user 消息
    - 更新会话时间
    返回 (conversation_row, message_row)
    """
    telegram_chat_id = event.chat_id
    language_code = getattr(user, "lang_code", None)

    db_user = repo.get_or_create_telegram_user(
        telegram_chat_id=telegram_chat_id,
        telegram_user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        language_code=language_code,
    )

    conv = repo.get_or_create_open_conversation(db_user["id"])
    msg = repo.insert_user_message(
        conversation_id=conv["id"],
        text=text,
        telegram_user_message_id=event.id,
    )
    repo.touch_conversation(conv["id"])

    return conv, msg


def bind_group_message(message_db_id: int, group_message_id: int) -> None:
    """
    收到内部群那边 send_message 的 message_id 之后，
    回填到 messages.telegram_group_message_id 里。
    """
    repo.update_message_group_id(message_db_id, group_message_id)


def handle_staff_reply(
    reply_to_message_id: int,
    staff,
    text: str,
    event,
) -> Optional[int]:
    """
    处理内部群里的回复：
    - 通过 reply_to_message_id 找到 messages 记录
    - 找到对应会话 + 用户
    - 插入一条 from_staff 消息
    - 返回目标用户的 telegram_chat_id（给 handler 去发消息）

    返回:
        int: target_chat_id，失败时返回 None
    """
    msg = repo.find_message_by_group_message_id(reply_to_message_id)
    if not msg:
        logger.warning("No message found for group_message_id=%s", reply_to_message_id)
        return None

    conv = repo.get_conversation_by_id(msg["conversation_id"])
    if not conv:
        logger.warning("No conversation found for id=%s", msg["conversation_id"])
        return None

    user = repo.get_telegram_user_by_id(conv["telegram_user_id"])
    if not user:
        logger.warning("No telegram_user found for id=%s", conv["telegram_user_id"])
        return None

    if not user.get("allow_contact", 1):
        logger.info(
            "User %s has allow_contact=0, skip sending reply",
            user["telegram_chat_id"],
        )
        return None

    staff_username = staff.username or (staff.first_name or "")

    repo.insert_staff_message(
        conversation_id=conv["id"],
        text=text,
        internal_staff_username=staff_username,
        telegram_group_message_id=event.id,
    )
    repo.touch_conversation(conv["id"])

    return user["telegram_chat_id"]


def handle_user_stop(telegram_chat_id: int) -> None:
    """
    用户发送 /stop 时调用，标记不再主动联系。
    """
    repo.set_user_allow_contact(telegram_chat_id, False)
