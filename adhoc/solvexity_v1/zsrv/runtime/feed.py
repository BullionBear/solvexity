from solvexity.trader.config import ConfigLoader
import solvexity.helper.logging as logging
from solvexity.helper.shutdown import Shutdown
import solvexity.helper as helper
import json

logger = logging.getLogger()

def feed_runtime(config_loader: ConfigLoader, shutdown: Shutdown, feed_service: str):

    provider = config_loader["feeds"][feed_service]
    shutdown.register(lambda frame: provider.close())
    # Start provider in a controlled loop
    try:
        for trigger in provider.send():
            trigger_message = json.loads(trigger)
            current_time = trigger_message["data"]["current_time"]
            logger.info(f"Datetime: {helper.to_isoformat(current_time)}")
    finally:
        shutdown.set()

    logger.info("Trading process terminated gracefully.")
