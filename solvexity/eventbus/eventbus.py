import asyncio
from typing import Callable

from solvexity.eventbus.event import Event


class EventBus:
    def __init__(self):
        self.subscribers: dict[str, list[Callable[[Event], None]]] = {}

    def subscribe(
        self, topic: str, callback: Callable[[Event], None]
    ) -> Callable[[], None]:
        if topic not in self.subscribers:
            self.subscribers[topic] = []
        self.subscribers[topic].append(callback)
        return lambda: self.subscribers[topic].remove(callback)

    async def publish(self, topic: str, event: Event) -> None:
        for callback in self.subscribers.get(topic, []):
            if asyncio.iscoroutinefunction(callback):
                await callback(event)
            else:
                callback(event)

    def list_events(self):
        return list(self.subscribers.keys())
    
