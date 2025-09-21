import logging
import asyncio
from solvexity.eventbus.eventbus import EventBus
from solvexity.feed.feed import Feed
from solvexity.strategy.strategy import Strategy

logger = logging.getLogger(__name__)

class Gateway:
    def __init__(self, strategy: Strategy, feeds: dict[str, Feed]):
        self.eventbus = EventBus()
        self.strategy = strategy
        self.feeds = feeds
        self.tasks: list[asyncio.Task] = []

    async def establish(self, source: str, method: str):
        if source not in self.feeds:
            raise ValueError(f"Feed {source} not found")
        if method not in dir(self.strategy):
            raise ValueError(f"Method {method} not found")
        self.eventbus.subscribe(method, getattr(self.strategy, method))
        self.tasks.append(asyncio.create_task(self.run(source, method)))

    async def run(self, source: str, method: str):
        async for event in self.feeds[source].recv():
            self.eventbus.publish(method, event)

    async def close(self):
        for task in self.tasks:
            task.cancel()









