import asyncio
from solvexity.collections.bouncing.bouncing import Bouncing
from solvexity.strategy.gateway import Gateway
from solvexity.feed.bar.binanceohlcv import BinanceOHLCV
from solvexity.eventbus.event import Event
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

async def main():
    strategy = Bouncing()
    gateway = Gateway(strategy)
    gateway.start()
    feed = BinanceOHLCV("BTCUSDT", "1m")
    async def publish(event: Event):
        await gateway.publish("on_bar", event)
    unsubscribe = await feed.subscribe(publish)
    # Wait for os.Interrupt
    try:
        while True:
            await asyncio.sleep(10)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt")
    logger.info("Stopping...")
    unsubscribe()
    gateway.stop()


if __name__ == "__main__":
    asyncio.run(main())