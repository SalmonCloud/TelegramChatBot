# src/app/telegram/handlers/command_handlers.py
import logging
from typing import List, Dict, Any

from telethon import events
from telethon.client.telegramclient import TelegramClient

from app.db import repositories as repo

logger = logging.getLogger(__name__)


def _format_server_list_for_city(
    city_display: str,
    country_display: str,
    rows: List[Dict[str, Any]],
) -> str:
    """
    把查询出来的服务器列表格式化成用户能看懂的文本。
    city_display / country_display 是给用户看的城市/国家名（可以写中文）。
    """
    if not rows:
        return f"当前 {city_display}（{country_display}）没有可用的独服库存。"

    lines: List[str] = []
    lines.append(f"{city_display}（{country_display}）当前可用独服：共 {len(rows)} 台\n")

    for idx, row in enumerate(rows, start=1):
        price = row.get("price_monthly_usd")
        # Decimal 也可以这么格式化
        price_str = f"{price:.2f}" if price is not None else "N/A"

        lines.append(
            f"{idx}. [{row.get('product_code', 'N/A')}]\n"
            f"   CPU: {row.get('cpu', 'N/A')}\n"
            f"   内存: {row.get('ram', 'N/A')}\n"
            f"   硬盘: {row.get('storage', 'N/A')}\n"
            f"   网卡: {row.get('nic', 'N/A')}\n"
            f"   价格: ${price_str} / 月\n"
        )

    return "\n".join(lines)


def register_command_handlers(client: TelegramClient):
    """
    注册所有 /命令 相关的 handler
    """

    # /bm_stock - 顶层命令：告诉用户可以用哪些子命令去查库存
    @client.on(events.NewMessage(pattern=r"^/bm_stock_(?:@\w+)?(?:\s|$)"))
    async def on_bm_stock(event):
        """
        顶层库存查询命令，只负责告诉用户下一步要用哪个命令。
        """
        text = (
            "【可交付独服库存查询】\n\n"
            "请根据机房位置选择一个具体的查询命令：\n"
            "  /bm_stock_hk  - 查询香港机房库存\n"
            "  /bm_stock_sjc - 查询圣何塞机房库存\n\n"
            "请直接点击上面的命令，或者复制到输入框重新发送。"
        )
        await event.reply(text)

    # /bm_stock_hk - 查询香港库存
    @client.on(events.NewMessage(pattern=r"^/bm_stock_hk(?:@\w+)?(?:\s|$)"))
    async def on_bm_stock_hk(event):
        """
        香港机房库存查询
        """
        try:
            rows = repo.get_available_servers_by_city_country(
                city="Hong Kong",
                country="China",
                limit=50,
            )
        except Exception:
            logger.exception("Failed to query server_info for Hong Kong")
            await event.reply("查询香港机房库存时出错，请稍后再试。")
            return

        reply_text = _format_server_list_for_city(
            city_display="香港",
            country_display="中国",
            rows=rows,
        )
        await event.reply(reply_text)

    # /bm_stock_sjc - 查询圣何塞库存（San Jose, United States）
    @client.on(events.NewMessage(pattern=r"^/bm_stock_sjc(?:@\w+)?(?:\s|$)"))
    async def on_bm_stock_sjc(event):
        """
        圣何塞机房库存查询
        """
        try:
            rows = repo.get_available_servers_by_city_country(
                city="San Jose",
                country="United States",
                limit=50,
            )
        except Exception:
            logger.exception("Failed to query server_info for San Jose")
            await event.reply("查询圣何塞机房库存时出错，请稍后再试。")
            return

        reply_text = _format_server_list_for_city(
            city_display="圣何塞 (San Jose)",
            country_display="美国",
            rows=rows,
        )
        await event.reply(reply_text)


    # /bw_price - 独服带宽价格查询
    @client.on(events.NewMessage(pattern=r"^/bw_price(?:@\w+)?(?:\s|$)"))
    async def on_bw_price(event):
        full_text = (event.raw_text or "").strip()
        parts = full_text.split(maxsplit=1)
        args = parts[1] if len(parts) > 1 else None

        # TODO: 在这里调用你的带宽价格查询逻辑
        # result = query_bw_price(args)

        reply_text = "【独服带宽价格查询】\n" \
                     "（这里以后接你的带宽价格逻辑，当前是占位回复）"
        if args:
            reply_text += f"\n你输入的参数：{args}"

        await event.reply(reply_text)
