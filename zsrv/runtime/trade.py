from solvexity.trader.config import ConfigLoader
import solvexity.helper.logging as logging
from solvexity.helper.shutdown import Shutdown
import solvexity.helper as helper
import time
import json

logger = logging.get_logger()

def trading_runtime(config_loader: ConfigLoader, shutdown: Shutdown, trade_service: str, feed_service: str, granular: str, n_live_granular: int = -1):
    strategy = config_loader["strategies"][trade_service]
    feed = config_loader["feeds"][feed_service]
    shutdown.register(lambda signum: strategy.close())
    shutdown.register(lambda signum: feed.close())
    try:
        for i, trigger in enumerate(feed.receive(granular)):
            if i == 0:
                end_time = feed.time() + n_live_granular * helper.to_unixtime_interval(granular)
                logger.info(f"Trading started at {helper.to_isoformat(end_time)}")
            if i >= n_live_granular >= 0: # n_live_granular < 0 means infinite
                shutdown.set()
            if shutdown.is_set():
                logger.info("Shutdown signal received.")
                break
            logger.info(f"Trigger Datetime: {helper.to_isoformat(trigger['data']['current_time'])}")
            strategy.invoke()
    except Exception as e:
        logger.error(f"Error in trading_runtime: {e}", exc_info=True)
    finally:
        shutdown.set()
        logger.info("Trading process terminated gracefully.")
