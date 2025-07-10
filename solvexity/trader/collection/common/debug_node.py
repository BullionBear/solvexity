from hooklet.base.pilot import PubSub
from hooklet.base.types import Msg
from hooklet.node.sinker import Sinker

class DebugNode(Sinker):
    def __init__(self, 
                 node_id: str,
                 subscribes: list[str],
                 pubsub: PubSub,
                 ):
        super().__init__(node_id, subscribes, pubsub)

    async def on_message(self, msg: Msg) -> None:
        self.logger.info(f"Received message: {msg}")