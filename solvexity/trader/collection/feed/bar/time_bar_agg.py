from hooklet.base import PubSub
from typing import Callable
from hooklet.base import Msg
from hooklet.node.pipe import Pipe
from typing import AsyncGenerator
import time

class TimeBarAgg(Pipe):
    def __init__(self, node_id: str,
                       subscribe: str,
                       interval_ms: int,
                       pubsub: PubSub, 
                       router: Callable[[Msg], str | None] = lambda msg: msg.type):
        super().__init__(node_id, [subscribe], pubsub, router)
        self.interval_ms = interval_ms
        self._start_time = int(time.time() * 1000)
        self._running_bar = None

    async def on_message(self, msg: Msg) -> AsyncGenerator[Msg, None]:
        if msg.type == "trade":
            