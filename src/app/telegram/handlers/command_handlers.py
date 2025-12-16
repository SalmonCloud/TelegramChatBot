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

    # 按 product_code 合并：展示首条配置，附上数量
    grouped: Dict[str, Dict[str, Any]] = {}
    order: List[str] = []
    for row in rows:
        code = row.get("product_code", "N/A")
        if code not in grouped:
            grouped[code] = {"row": row, "count": 1}
            order.append(code)
        else:
            grouped[code]["count"] += 1

    total_count = len(rows)
    lines: List[str] = []
    lines.append(f"{city_display}（{country_display}）当前可用独服：共 {total_count} 台\n")

    for idx, code in enumerate(order, start=1):
        entry = grouped[code]
        row = entry["row"]
        count = entry["count"]

        price = row.get("price_monthly_usd")
        price_str = f"{price:.2f}" if price is not None else "N/A"

        lines.append(
            f"{idx}. [{row.get('product_code', 'N/A')}]\n"
            f"   CPU: {row.get('cpu', 'N/A')}\n"
            f"   内存: {row.get('total_ram', 'N/A')}\n"
            f"   硬盘: {row.get('storage', 'N/A')}\n"
            f"   网卡: {row.get('nic', 'N/A')}\n"
            f"   赠送带宽: {row.get('included_bandwidth', 'N/A')}\n"
            f"   数量: {count} 台\n"
            f"   价格: ${price_str} / 月\n"
        )

    return "\n".join(lines)


def _format_bandwidth_list_for_city(
    city_display: str,
    country_display: str,
    rows: List[Dict[str, Any]],
) -> str:
    """
    把某个城市下所有机房的带宽价格列表，格式化成文本。
    会按 datacenter 分组。
    """
    if not rows:
        return f"当前 {city_display}（{country_display}）没有带宽价格数据。"

    # 按机房分组
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for row in rows:
        dc_code = row.get("datacenter_code") or "N/A"
        grouped.setdefault(dc_code, []).append(row)

    lines: List[str] = []
    lines.append(f"{city_display}（{country_display}）带宽价格：\n")

    for dc_code, dc_rows in grouped.items():
        dc_name = dc_rows[0].get("datacenter_name") or ""
        header = f"机房 {dc_code}"
        if dc_name:
            header += f"（{dc_name}）"
        lines.append(header)

        for r in dc_rows:
            min_bw = r.get("min_bandwidth_gbps")
            max_bw = r.get("max_bandwidth_gbps")

            if min_bw is None and max_bw is None:
                range_str = "带宽不限"
            elif min_bw is None:
                range_str = f"< {max_bw} Gbps"
            elif max_bw is None:
                range_str = f">= {min_bw} Gbps"
            else:
                range_str = f"{min_bw}–{max_bw} Gbps"

            flat = r.get("flat_price_usd_per_mbps")
            commit = r.get("commit_price_usd_per_mbps")
            over = r.get("overage_price_usd_per_mbps")

            lines.append(
                f"  - {r.get('tier_label', range_str)}："
                f"平价 ${flat:.3f}/Mbps，"
                f"保底 ${commit:.3f}/Mbps，"
                f"超量 ${over:.3f}/Mbps"
            )

        lines.append("")  # 机房之间空一行

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

    # /bw_price_ - 顶层带宽价格查询命令
    @client.on(events.NewMessage(pattern=r"^/bw_price_(?:@\w+)?(?:\s|$)"))
    async def on_bw_price_root(event):
        """
        顶层带宽价格查询命令，只负责告诉用户下一步要用哪个命令。
        """
        text = (
            "【独服带宽价格查询】\n\n"
            "请根据机房位置选择一个具体的查询命令：\n"
            "  /bw_price_hk  - 查询香港机房带宽价格\n"
            "  /bw_price_sjc - 查询圣何塞机房带宽价格\n\n"
            "请直接点击上面的命令，或者复制到输入框重新发送。"
        )
        await event.reply(text)

    # /bw_price_hk - 香港带宽价格
    @client.on(events.NewMessage(pattern=r"^/bw_price_hk(?:@\w+)?(?:\s|$)"))
    async def on_bw_price_hk(event):
        try:
            rows = repo.get_bandwidth_pricing_by_city_country(
                city="Hong Kong",
                country="China",
                limit=100,
            )
        except Exception:
            logger.exception("Failed to query bandwidth_pricing for Hong Kong")
            await event.reply("查询香港机房带宽价格时出错，请稍后再试。")
            return

        reply_text = _format_bandwidth_list_for_city(
            city_display="香港",
            country_display="中国",
            rows=rows,
        )
        await event.reply(reply_text)

    # /bw_price_sjc - 圣何塞带宽价格
    @client.on(events.NewMessage(pattern=r"^/bw_price_sjc(?:@\w+)?(?:\s|$)"))
    async def on_bw_price_sjc(event):
        try:
            rows = repo.get_bandwidth_pricing_by_city_country(
                city="San Jose",
                country="United States",
                limit=100,
            )
        except Exception:
            logger.exception("Failed to query bandwidth_pricing for San Jose")
            await event.reply("查询圣何塞机房带宽价格时出错，请稍后再试。")
            return

        reply_text = _format_bandwidth_list_for_city(
            city_display="圣何塞 (San Jose)",
            country_display="美国",
            rows=rows,
        )
        await event.reply(reply_text)
