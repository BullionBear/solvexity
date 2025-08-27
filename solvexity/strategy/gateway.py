from solvexity.eventbus import EventBus, Event
from solvexity.strategy.strategy import Strategy
import logging

logger = logging.getLogger(__name__)

class Gateway:
    def __init__(self, strategy: Strategy):
        self.eventbus = EventBus()
        self.strategy = strategy
        self._unsubscribe_functions = []

    def start(self):
        for attr in dir(self.strategy):
            if attr.startswith("on_"):
                logger.info(f"Subscribing to {attr}")
                unsubscribe_function = self.eventbus.subscribe(attr, getattr(self.strategy, attr))
                self._unsubscribe_functions.append(unsubscribe_function)

    def stop(self):
        for unsubscribe_function in self._unsubscribe_functions:
            unsubscribe_function()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop()

    def list_events(self):
        return self.eventbus.list_events()
    
    async def publish(self, topic: str, event: Event):
        await self.eventbus.publish(topic, event.data)
