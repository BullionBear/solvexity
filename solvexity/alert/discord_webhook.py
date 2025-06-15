import enum
import logging
import time
from typing import Any, Dict, List, Optional, Union

import aiohttp

logger = logging.getLogger(__name__)


class DiscordColor(enum.IntEnum):
    """Discord message color codes"""

    RED = 0xFF0000
    GREEN = 0x00FF00
    BLUE = 0x0000FF
    YELLOW = 0xFFFF00
    PURPLE = 0x800080
    ORANGE = 0xFFA500
    TEAL = 0x008080
    WHITE = 0xFFFFFF


class DiscordWebhook:
    """
    Discord webhook client for sending notifications to Discord channels.
    Supports text messages, embeds, and customizable formatting.
    Uses async methods for non-blocking webhook notifications.
    """

    def __init__(self, webhook_url: str, username: str = None, avatar_url: str = None):
        """
        Initialize Discord webhook client.

        Args:
            webhook_url: Discord webhook URL
            username: Override webhook's default username
            avatar_url: Override webhook's default avatar
        """
        self.webhook_url = webhook_url
        self.username = username
        self.avatar_url = avatar_url

    async def send_message(self, content: str) -> bool:
        """
        Send a simple text message to Discord.

        Args:
            content: The message text to send

        Returns:
            bool: Success status
        """
        payload = {"content": content}

        if self.username:
            payload["username"] = self.username

        if self.avatar_url:
            payload["avatar_url"] = self.avatar_url

        return await self._send_request(payload)

    async def send_embed(
        self,
        title: str,
        description: Optional[str] = None,
        color: Union[DiscordColor, int] = DiscordColor.BLUE,
        fields: Optional[List[Dict[str, str]]] = None,
        thumbnail_url: Optional[str] = None,
        image_url: Optional[str] = None,
        footer_text: Optional[str] = None,
        timestamp: Optional[int] = None,
    ) -> bool:
        """
        Send an embed message to Discord with rich formatting.

        Args:
            title: Embed title
            description: Embed description text
            color: Color of the embed sidebar (use DiscordColor enum or int)
            fields: List of field dicts with {'name': 'Field Name', 'value': 'Field Value', 'inline': True/False}
            thumbnail_url: URL for small thumbnail image
            image_url: URL for main embed image
            footer_text: Text to display in footer
            timestamp: Unix timestamp or None for current time

        Returns:
            bool: Success status
        """
        if timestamp is None:
            # Current time in ISO8601 format
            timestamp = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())
        elif isinstance(timestamp, int):
            # Convert Unix timestamp to ISO8601
            timestamp = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime(timestamp))

        embed = {"title": title, "color": int(color), "timestamp": timestamp}

        if description:
            embed["description"] = description

        if fields:
            embed["fields"] = fields

        if thumbnail_url:
            embed["thumbnail"] = {"url": thumbnail_url}

        if image_url:
            embed["image"] = {"url": image_url}

        if footer_text:
            embed["footer"] = {"text": footer_text}

        payload = {"embeds": [embed]}

        if self.username:
            payload["username"] = self.username

        if self.avatar_url:
            payload["avatar_url"] = self.avatar_url

        return await self._send_request(payload)

    async def send_alert(
        self,
        title: str,
        message: str,
        is_success: bool = True,
        details: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Send a standardized alert message with status indicator.

        Args:
            title: Alert title
            message: Alert message
            is_success: True for success (green), False for failure (red)
            details: Optional dict of key-value details to include as fields

        Returns:
            bool: Success status
        """
        color = DiscordColor.GREEN if is_success else DiscordColor.RED
        status = "✅ Success" if is_success else "❌ Failure"

        fields = []
        if details:
            for key, value in details.items():
                fields.append({"name": key, "value": str(value), "inline": True})

        return await self.send_embed(
            title=f"{status}: {title}",
            description=message,
            color=color,
            fields=fields,
            timestamp=int(time.time()),
        )

    async def send_trade_notification(
        self,
        symbol: str,
        side: str,
        price: float,
        amount: float,
        trade_id: Optional[str] = None,
    ) -> bool:
        """
        Send a trade execution notification.

        Args:
            symbol: Trading pair symbol (e.g., 'BTC/USDT')
            side: Trade side ('buy' or 'sell')
            price: Execution price
            amount: Trade amount
            trade_id: Optional trade identifier

        Returns:
            bool: Success status
        """
        side = side.lower()
        is_buy = side == "buy"
        color = DiscordColor.GREEN if is_buy else DiscordColor.RED
        emoji = "🟢" if is_buy else "🔴"

        fields = [
            {"name": "Symbol", "value": symbol, "inline": True},
            {"name": "Side", "value": f"{emoji} {side.upper()}", "inline": True},
            {"name": "Price", "value": f"{price:.8f}", "inline": True},
            {"name": "Amount", "value": f"{amount:.8f}", "inline": True},
            {"name": "Total", "value": f"{price * amount:.8f}", "inline": True},
        ]

        if trade_id:
            fields.append({"name": "Trade ID", "value": trade_id, "inline": False})

        return await self.send_embed(
            title=f"Trade Execution: {symbol}",
            color=color,
            fields=fields,
            timestamp=int(time.time()),
        )

    async def send_price_alert(
        self, symbol: str, price: float, threshold: float, condition: str
    ) -> bool:
        """
        Send a price alert notification.

        Args:
            symbol: Trading pair symbol (e.g., 'BTC/USDT')
            price: Current price
            threshold: Alert threshold value
            condition: Alert condition ('above', 'below', etc.)

        Returns:
            bool: Success status
        """
        title = f"Price Alert: {symbol}"
        description = f"**{symbol}** price is {condition} {threshold}: **{price:.8f}**"

        return await self.send_embed(
            title=title,
            description=description,
            color=DiscordColor.YELLOW,
            timestamp=int(time.time()),
        )

    async def _send_request(self, payload: Dict[str, Any]) -> bool:
        """
        Send HTTP request to Discord webhook endpoint asynchronously.

        Args:
            payload: Discord webhook payload

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload) as response:
                    if response.status == 204:
                        logger.info("Discord notification sent successfully")
                        return True
                    else:
                        response_text = await response.text()
                        logger.error(
                            f"Failed to send Discord notification: HTTP {response.status}"
                        )
                        logger.error(f"Response: {response_text}")
                        return False
        except Exception as e:
            logger.exception(f"Error sending Discord notification: {str(e)}")
            return False
