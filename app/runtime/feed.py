from trader.config import ConfigLoader
from helper import Shutdown
import helper.logging as logging

logger = logging.getLogger("feed")

def feed_runtime(config_loader: ConfigLoader, shutdown: Shutdown, data_service: str):
    
    # Start provider in a controlled loop
    try:
        provider = config_loader["feeds"][data_service]
        shutdown.register(lambda signum: provider.stop()) # avoid provider refereced before assignment
        for data in provider.send():
            if shutdown.is_set():
                break
            logger.info(f"Publish kline data: {data}")
    finally:
        logger.info("Trading process terminated gracefully.")