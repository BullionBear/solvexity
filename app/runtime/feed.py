from trader.config import ConfigLoader
from helper import Shutdown
import helper.logging as logging
import signal

shutdown = Shutdown(signal.SIGINT, signal.SIGTERM)
logger = logging.getLogger("feed")

def feed_runtime(config_loader: ConfigLoader, data_service: str):
    provider = config_loader["feed"][data_service]
    # Start provider in a controlled loop
    try:
        for data in provider.send():
            if shutdown.is_set():
                break
            logger.info(f"Publish kline data: {data}")
    finally:
        provider.stop()

    logger.info("Trading process terminated gracefully.")