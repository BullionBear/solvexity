from solvexity.trader.config import ConfigLoader
import solvexity.helper.logging as logging
from solvexity.helper.shutdown import Shutdown
import solvexity.helper as helper
import time
import json

logger = logging.getLogger()

def trading_runtime(config_loader: ConfigLoader, shutdown: Shutdown, trade_service: str, feed_service: str, granular: str, n_live_granular: int = -1):
    strategy = config_loader["strategies"][trade_service]
    feed = config_loader["feeds"][feed_service]
    shutdown.register(lambda signum: feed.close())
    shutdown.register(lambda signum: strategy.close())
    end_time = float('inf')
    logger.info(f"Trading will never end")
    try:
        for i, trigger in enumerate(feed.receive(granular)):
            if i == 0 and n_live_granular > 0:
                end_time = feed.time() + n_live_granular * helper.to_unixtime_interval(granular)
            if feed.time() > end_time:
                shutdown.set()
            if shutdown.is_set():
                break
            logger.info(f"Trigger Datetime: {helper.to_isoformat(trigger['data']['current_time'])}")

            strategy.invoke()
    finally:
        shutdown.set()
        logger.info("Trading process terminated gracefully.")
