from trader.config import ConfigLoader
import helper.logging as logging
from helper.shutdown import Shutdown

logger = logging.getLogger("feed")

def feed_runtime(config_loader: ConfigLoader, shutdown: Shutdown, feed_service: str):

    provider = config_loader["feeds"][feed_service]
    # Start provider in a controlled loop
    try:
        for data in provider.send():
            if shutdown.is_set():
                break
            logger.info(f"Publish kline data: {data}")
    finally:
        shutdown.set()
        provider.close()

    logger.info("Trading process terminated gracefully.")