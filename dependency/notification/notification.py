import enum
from typing import Callable, Dict, Optional, Any
import requests
import helper.logging as logging


logger = logging.getLogger("data")


def send_notification(webhook_url, content, username, embed=None):
    data = {
        "content": content,
        "username": username,
        "embeds": [embed] if embed else []
    }

    response = requests.post(webhook_url, json=data)

    if response.status_code == 204:
        logger.info("Notification sent successfully!")
    else:
        logger.error(f"Failed to send notification: {response.status_code}")
        logger.error(response.text)


class Color(enum.IntEnum):
    # Common colors with their RGB 24-bit integer values
    RED = 0xFF0000        # Decimal: 16711680
    GREEN = 0x00FF00      # Decimal: 65280
    BLUE = 0x0000FF       # Decimal: 255
    YELLOW = 0xFFFF00     # Decimal: 16776960
    CYAN = 0x00FFFF       # Decimal: 65535
    MAGENTA = 0xFF00FF    # Decimal: 16711935
    WHITE = 0xFFFFFF      # Decimal: 16777215
    BLACK = 0x000000      # Decimal: 0
    ORANGE = 0xFFA500     # Decimal: 16753920
    PURPLE = 0x800080     # Decimal: 8388736
    GRAY = 0x808080       # Decimal: 8421504


class Notification:
    def __init__(self, webhook: str, enabled: bool = True):
        self.webhook = webhook
        self.enabled = enabled

    def notify(self, username: str, title: str, content: Optional[str], color: Color):
        embed = {
            "title": title,
            "description": content,
            "color": color
        }
        logger.info(f"Sending notification to {title=}")
        if self.enabled:
            send_notification(self.webhook, None, username, embed)
