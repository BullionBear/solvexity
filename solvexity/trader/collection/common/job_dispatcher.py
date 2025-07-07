from hooklet.node.worker import Dispatcher, PushPull, Job, Msg
from hooklet.node.sinker import Sinker

class JobDispatcher(Sinker):
    def __init__(self, 
                 node_id: str,
                 subscribes: list[str],
                 pushpull: PushPull,
                 dispatch_to: str,
                 ):
        super().__init__(node_id, subscribes)
        self.dispatcher = Dispatcher(pushpull)
        self.dispatch_to = dispatch_to


    async def start(self) -> None:
        await super().start()
        async def log_msg(job: Job) -> None:
            self.logger.info(f"Received job: {job}")
        await self.dispatcher.subscribe(self.dispatch_to, log_msg)

    async def sink(self, msg: Msg) -> None:
        if msg.type == "trade":
            job = Job(
                id=msg.id,
                type=msg.type,
                data=msg.data,
                error=None,
                recv_ms=0,
                start_ms=0,
                end_ms=0,
                status="pending",
                retry_count=0,
            )
            await self.dispatcher.dispatch(job)
            self.logger.info(f"Dispatched job: {job} to {self.dispatch_to}")
        else:
            self.logger.error(f"Invalid message type: {msg.type}")

    async def on_finish(self) -> None:
        await self.dispatcher.unsubscribe(self.dispatch_to)
        await super().on_finish()
