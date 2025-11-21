from typing import Dict, Any
from telethon.tl.types import User


def _display_name(user: User) -> str:
    parts = []
    if user.first_name:
        parts.append(user.first_name)
    if user.last_name:
        parts.append(user.last_name)
    if parts:
        return " ".join(parts)
    if user.username:
        return f"@{user.username}"
    return "未知用户"


def format_new_customer_message(
    conv: Dict[str, Any],
    msg: Dict[str, Any],
    user: User,
    telegram_chat_id: int,
) -> str:
    """
    生成发到内部群的“新客户消息”卡片文案。
    """
    name = _display_name(user)
    username = f"@{user.username}" if user.username else "(没有用户名)"

    text_preview = (msg.get("text") or "").strip()
    if len(text_preview) > 400:
        text_preview = text_preview[:400] + "..."

    return (
        "📨 新客户消息\n"
        f"会话ID：#{conv['id']}\n"
        f"客户：{name} {username}\n"
        f"Telegram chat id：{telegram_chat_id}\n"
        "------------------------------\n"
        f"{text_preview}"
    )
