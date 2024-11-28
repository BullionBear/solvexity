import asyncio
from trader.config import ConfigLoader
import helper.logging as logging

logger = logging.getLogger("feed")

async def feed_runtime(config_loader, feed_service: str):
    provider = config_loader["feeds"][feed_service]

    async def run_provider():
        while True:
            # Retrieve the generator from provider.send()
            generator = await asyncio.to_thread(provider.send)
            for data in generator:  # Iterate over the generator to get values
                logger.info(f"Publish kline data: {data}")

    try:
        await run_provider()
    except asyncio.CancelledError:
        logger.info("Feed runtime was cancelled.")
        provider.close()
    
