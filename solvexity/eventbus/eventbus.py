import asyncio
from typing import Callable

from solvexity.eventbus.event import Event


class EventBus:
    def __init__(self):
        self.subscribers: dict[str, list[Callable[[Event], None]]] = {}

    def subscribe(self, source: str, callback: Callable[[Event], None]) -> Callable[[], None]:
        if source not in self.subscribers:
            self.subscribers[source] = []
        self.subscribers[source].append(callback)
        return lambda: self.subscribers[source].remove(callback)

    def publish(self, event: Event) -> None:
        for callback in self.subscribers.get(event.source, []):
            if asyncio.iscoroutinefunction(callback):
                asyncio.create_task(callback(event))
            else:
                callback(event)

    async def publish_async(self, event: Event) -> None:
        for callback in self.subscribers.get(event.source, []):
            if asyncio.iscoroutinefunction(callback):
                await callback(event)
            else:
                callback(event)