import logging
from typing import Optional, Dict, Any, List

from app.db.connection import get_connection

logger = logging.getLogger(__name__)


# ========== 基础工具 ==========

def _fetch_one(cursor) -> Optional[Dict[str, Any]]:
    row = cursor.fetchone()
    return row if row else None


def _fetch_all(cursor) -> List[Dict[str, Any]]:
    rows = cursor.fetchall()
    return rows or []


# ========== telegram_users 相关 ==========

def get_or_create_telegram_user(
    telegram_chat_id: int,
    username: Optional[str],
    first_name: Optional[str],
    last_name: Optional[str],
    telegram_user_id: Optional[int] = None,
    language_code: Optional[str] = None,
) -> Dict[str, Any]:
    """
    根据 telegram_chat_id 查找用户，不存在则创建。
    返回 telegram_users 表中的整行数据（dict）。
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # 1. 先查
            cur.execute(
                """
                SELECT *
                FROM telegram_users
                WHERE telegram_chat_id = %s
                LIMIT 1
                """,
                (telegram_chat_id,),
            )
            row = _fetch_one(cur)
            if row:
                # 如果有变化，顺手更新一下用户名等信息（不是必须，但比较干净）
                need_update = False
                update_fields = []
                params = []

                if username is not None and row.get("username") != username:
                    need_update = True
                    update_fields.append("username = %s")
                    params.append(username)

                if first_name is not None and row.get("first_name") != first_name:
                    need_update = True
                    update_fields.append("first_name = %s")
                    params.append(first_name)

                if last_name is not None and row.get("last_name") != last_name:
                    need_update = True
                    update_fields.append("last_name = %s")
                    params.append(last_name)

                if telegram_user_id is not None and row.get("telegram_user_id") != telegram_user_id:
                    need_update = True
                    update_fields.append("telegram_user_id = %s")
                    params.append(telegram_user_id)

                if language_code is not None and row.get("language_code") != language_code:
                    need_update = True
                    update_fields.append("language_code = %s")
                    params.append(language_code)

                if need_update:
                    params.append(telegram_chat_id)
                    sql = f"""
                        UPDATE telegram_users
                        SET {", ".join(update_fields)},
                            updated_at = NOW()
                        WHERE telegram_chat_id = %s
                    """
                    cur.execute(sql, tuple(params))
                    conn.commit()

                    # 再读一次最新的
                    cur.execute(
                        """
                        SELECT *
                        FROM telegram_users
                        WHERE telegram_chat_id = %s
                        LIMIT 1
                        """,
                        (telegram_chat_id,),
                    )
                    row = _fetch_one(cur)

                return row

            # 2. 不存在则插入
            cur.execute(
                """
                INSERT INTO telegram_users
                    (telegram_chat_id, telegram_user_id, username, first_name, last_name, language_code)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (telegram_chat_id, telegram_user_id, username, first_name, last_name, language_code),
            )
            conn.commit()
            user_id = cur.lastrowid

            cur.execute(
                "SELECT * FROM telegram_users WHERE id = %s LIMIT 1",
                (user_id,),
            )
            row = _fetch_one(cur)
            return row
    finally:
        conn.close()


def get_telegram_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """
    根据 telegram_users.id 获取用户。
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM telegram_users WHERE id = %s LIMIT 1",
                (user_id,),
            )
            return _fetch_one(cur)
    finally:
        conn.close()


def get_telegram_user_by_chat_id(telegram_chat_id: int) -> Optional[Dict[str, Any]]:
    """
    根据 telegram_chat_id 获取用户。
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM telegram_users WHERE telegram_chat_id = %s LIMIT 1",
                (telegram_chat_id,),
            )
            return _fetch_one(cur)
    finally:
        conn.close()


def set_user_allow_contact(telegram_chat_id: int, allow: bool) -> None:
    """
    设置用户是否允许再联系。
    注意：这里参数是 telegram_chat_id（和你 Telethon 里的私聊 chat_id 相同）
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE telegram_users
                SET allow_contact = %s,
                    updated_at = NOW()
                WHERE telegram_chat_id = %s
                """,
                (1 if allow else 0, telegram_chat_id),
            )
            conn.commit()
    finally:
        conn.close()


# ========== conversations 相关 ==========

def get_or_create_open_conversation(telegram_user_pk_id: int) -> Dict[str, Any]:
    """
    获取该用户最近一个 status 为 open/in_progress 的会话，如果没有就创建一个新的 open 会话。
    参数 telegram_user_pk_id 是 telegram_users.id（不是 chat_id）。
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # 1. 查找已有 open 或 in_progress 会话
            cur.execute(
                """
                SELECT *
                FROM conversations
                WHERE telegram_user_id = %s
                  AND status IN ('open', 'in_progress')
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (telegram_user_pk_id,),
            )
            row = _fetch_one(cur)
            if row:
                return row

            # 2. 没有则创建新的 open 会话
            cur.execute(
                """
                INSERT INTO conversations
                    (telegram_user_id, status, created_at, updated_at, last_message_at)
                VALUES (%s, 'open', NOW(), NOW(), NOW())
                """,
                (telegram_user_pk_id,),
            )
            conn.commit()
            conv_id = cur.lastrowid

            cur.execute(
                """
                SELECT *
                FROM conversations
                WHERE id = %s
                LIMIT 1
                """,
                (conv_id,),
            )
            row = _fetch_one(cur)
            return row
    finally:
        conn.close()


def get_conversation_by_id(conversation_id: int) -> Optional[Dict[str, Any]]:
    """
    根据会话 ID 获取会话。
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM conversations WHERE id = %s LIMIT 1",
                (conversation_id,),
            )
            return _fetch_one(cur)
    finally:
        conn.close()


def touch_conversation(conversation_id: int) -> None:
    """
    更新会话的 last_message_at 为当前时间。
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE conversations
                SET last_message_at = NOW(),
                    updated_at = NOW()
                WHERE id = %s
                """,
                (conversation_id,),
            )
            conn.commit()
    finally:
        conn.close()


def update_conversation_status(conversation_id: int, status: str) -> None:
    """
    修改会话状态，比如 'open', 'in_progress', 'closed'。
    如果你以后要做 /close 命令可以用这个。
    """
    if status not in ("open", "in_progress", "closed"):
        raise ValueError(f"invalid conversation status: {status}")

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            if status == "closed":
                cur.execute(
                    """
                    UPDATE conversations
                    SET status = %s,
                        closed_at = NOW(),
                        updated_at = NOW()
                    WHERE id = %s
                    """,
                    (status, conversation_id),
                )
            else:
                cur.execute(
                    """
                    UPDATE conversations
                    SET status = %s,
                        updated_at = NOW()
                    WHERE id = %s
                    """,
                    (status, conversation_id),
                )
            conn.commit()
    finally:
        conn.close()


# ========== messages 相关 ==========

def insert_user_message(
    conversation_id: int,
    text: Optional[str],
    telegram_user_message_id: Optional[int] = None,
    telegram_group_message_id: Optional[int] = None,
    content_type: str = "text",
    raw_payload: Optional[str] = None,
) -> Dict[str, Any]:
    """
    插入一条来自用户的消息（from_user）。
    返回 messages 表中的整行数据。
    """
    if content_type not in ("text", "photo", "document", "audio", "video", "sticker", "other"):
        content_type = "other"

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO messages
                    (conversation_id, direction, content_type,
                     text, telegram_user_message_id, telegram_group_message_id,
                     internal_staff_username, raw_payload, created_at)
                VALUES (%s, 'from_user', %s,
                        %s, %s, %s,
                        NULL, %s, NOW())
                """,
                (
                    conversation_id,
                    content_type,
                    text,
                    telegram_user_message_id,
                    telegram_group_message_id,
                    raw_payload,
                ),
            )
            conn.commit()
            msg_id = cur.lastrowid

            cur.execute(
                "SELECT * FROM messages WHERE id = %s LIMIT 1",
                (msg_id,),
            )
            return _fetch_one(cur)
    finally:
        conn.close()


def insert_staff_message(
    conversation_id: int,
    text: Optional[str],
    internal_staff_username: Optional[str] = None,
    telegram_group_message_id: Optional[int] = None,
    content_type: str = "text",
    raw_payload: Optional[str] = None,
    telegram_user_message_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    插入一条来自内部同事的消息（from_staff）。
    返回 messages 表中的整行数据。
    """
    if content_type not in ("text", "photo", "document", "audio", "video", "sticker", "other"):
        content_type = "other"

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO messages
                    (conversation_id, direction, content_type,
                     text, telegram_user_message_id, telegram_group_message_id,
                     internal_staff_username, raw_payload, created_at)
                VALUES (%s, 'from_staff', %s,
                        %s, %s, %s,
                        %s, %s, NOW())
                """,
                (
                    conversation_id,
                    content_type,
                    text,
                    telegram_user_message_id,
                    telegram_group_message_id,
                    internal_staff_username,
                    raw_payload,
                ),
            )
            conn.commit()
            msg_id = cur.lastrowid

            cur.execute(
                "SELECT * FROM messages WHERE id = %s LIMIT 1",
                (msg_id,),
            )
            return _fetch_one(cur)
    finally:
        conn.close()


def update_message_group_id(msg_id: int, group_message_id: int) -> None:
    """
    在我们已经插入了一条来自用户的消息后，
    收到内部群那边 send_message 的 message_id，再回填到 telegram_group_message_id 里。
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE messages
                SET telegram_group_message_id = %s
                WHERE id = %s
                """,
                (group_message_id, msg_id),
            )
            conn.commit()
    finally:
        conn.close()


def find_message_by_group_message_id(group_message_id: int) -> Optional[Dict[str, Any]]:
    """
    通过内部群 message_id 找到我们之前记录的那条 messages 记录。
    主要用于：同事 reply 那条群消息时，找到对应会话。
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT *
                FROM messages
                WHERE telegram_group_message_id = %s
                LIMIT 1
                """,
                (group_message_id,),
            )
            return _fetch_one(cur)
    finally:
        conn.close()


# ========== server_info（服务器库存）相关 ==========

def get_available_servers_by_city_country(
    city: str,
    country: str,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """
    从 server_info 表中按城市+国家查询当前可用的服务器列表。
    只返回 available = 1 的记录，按价格从低到高排序。
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    city,
                    country,
                    product_code,
                    cpu,
                    total_ram,
                    storage,
                    nic,
                    price_monthly_usd,
                    available,
                    created_at,
                    updated_at
                FROM server_info
                WHERE city = %s
                  AND country = %s
                  AND available = 1
                ORDER BY price_monthly_usd ASC, id ASC
                LIMIT %s
                """,
                (city, country, limit),
            )
            return _fetch_all(cur)
    finally:
        conn.close()


# ========== bandwidth_pricing（带宽价格）相关 ==========

def get_bandwidth_pricing_by_city_country(
    city: str,
    country: str,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """
    从 bandwidth_pricing 表中按城市+国家查询带宽价格列表。
    返回指定城市/国家下所有机房、所有带宽档位。
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    country,
                    city,
                    datacenter_code,
                    datacenter_name,
                    tier_label,
                    min_bandwidth_gbps,
                    max_bandwidth_gbps,
                    flat_price_usd_per_mbps,
                    commit_price_usd_per_mbps,
                    overage_price_usd_per_mbps,
                    created_at,
                    updated_at
                FROM bandwidth_pricing
                WHERE city = %s
                  AND country = %s
                ORDER BY
                    datacenter_code ASC,
                    min_bandwidth_gbps ASC,
                    max_bandwidth_gbps ASC,
                    id ASC
                LIMIT %s
                """,
                (city, country, limit),
            )
            return _fetch_all(cur)
    finally:
        conn.close()