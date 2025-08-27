import asyncio
from solvexity.collections.bouncing.bouncing import Bouncing
from solvexity.strategy.gateway import Gateway
from solvexity.feed.bar.binanceohlcv import BinanceOHLCV
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

async def main():
    strategy = Bouncing()
    gateway = Gateway(strategy)
    gateway.start()
    feed = BinanceOHLCV("BTCUSDT", "1m")
    unsubscribe = await feed.subscribe(lambda event: gateway.publish("on_bar", event))
    await asyncio.sleep(10)
    unsubscribe()
    gateway.stop()


if __name__ == "__main__":
    asyncio.run(main())