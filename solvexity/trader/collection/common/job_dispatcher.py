from hooklet.node.worker import Dispatcher, PushPull
from hooklet.base.pilot import PubSub
from hooklet.base.types import Job, Msg
from hooklet.node.sinker import Sinker
import uuid


class JobDispatcher(Sinker):
    def __init__(self, 
                 node_id: str,
                 subscribes: list[str],
                 pubsub: PubSub,
                 pushpull: PushPull,
                 dispatch_to: str,
                 ):
        super().__init__(node_id, subscribes, pubsub)
        self.dispatcher = Dispatcher(pushpull)
        self.dispatch_to = dispatch_to


    async def on_start(self) -> None:
        await super().on_start()
        async def log_msg(job: Job) -> None:
            self.logger.info(f"Received job: {job}")
        await self.dispatcher.subscribe(self.dispatch_to, log_msg)

    async def on_message(self, msg: Msg) -> None:
        self.logger.info(f"Received message: {msg}")
        if msg.type == "trade":
            job = Job(
                id=msg.id,
                type=msg.type,
                data=msg.data,
                error=None,
                recv_ms=0,
                start_ms=0,
                end_ms=0,
                status="new",
                retry_count=0,
            )
            await self.dispatcher.dispatch(self.dispatch_to, job)
            self.logger.info(f"Dispatched job: {job} to {self.dispatch_to}")
        else:
            self.logger.error(f"Invalid message type: {msg.type}")

    async def on_close(self) -> None:
        await self.dispatcher.unsubscribe(self.dispatch_to)
        await super().on_close()
