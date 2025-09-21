import asyncio
from typing import Callable
import nats
import logging
import uuid

logger = logging.getLogger(__name__)

class NatsEventBus:
    def __init__(self, nats_urls: list[str]):
        self.nats_urls = nats_urls
        self.subscriptions: dict[int, nats.Subscription] = {}

    async def connect(self):
        self.nc = await nats.connect(servers=self.nats_urls)
        logger.info(f"Connected to NATS at {self.nats_urls}")

    async def subscribe(self, topic: str, callback: Callable[[nats.Msg], None]) -> int:
        sub = await self.nc.subscribe(topic, callback)
        subscript_id = uuid.uuid4().int
        self.subscriptions[subscript_id] = sub
        logger.info(f"Subscribed to {topic}")
        return subscript_id
    
    async def unsubscribe(self, subscript_id: int):
        sub = self.subscriptions.pop(subscript_id)
        await sub.unsubscribe()
        logger.info(f"Unsubscribed from {sub.subject}")

    async def disconnect(self):
        await self.nc.close()
        logger.info("Disconnected from NATS")
