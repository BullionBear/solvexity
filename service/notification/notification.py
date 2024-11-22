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

class Notification:
    def __init__(self, webhook: str):
        self.webhook = webhook

    def notify(self, content, username="Notification Bot", embed=None):
        send_notification(self.webhook, content, username, embed)