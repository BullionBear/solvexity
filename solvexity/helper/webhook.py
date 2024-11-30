import requests
from .logging import getLogger

logger = getLogger()


def send_notification(webhook_url, content, username="Notification Bot", embed=None):
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