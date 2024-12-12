from solvexity.trader.config import ConfigLoader
import solvexity.helper.logging as logging
from solvexity.helper.shutdown import Shutdown
import solvexity.helper as helper
import time
import json

logger = logging.getLogger()

def trading_runtime(config_loader: ConfigLoader, shutdown: Shutdown, trade_service: str, feed_service: str, granular: str, n_live_granular: int = -1):
    strategy = config_loader["strategies"][trade_service]
    provider = config_loader["feeds"][feed_service]
    shutdown.register(lambda signum: provider.close())
    shutdown.register(lambda signum: strategy.close())
    if n_live_granular > 0:
        end_time = time.time() + helper.to_unixtime_interval(granular) * n_live_granular
        logger.info(f"Trading will end at: {helper.to_isoformat(end_time)}")
    else:
        end_time = float("inf")
        logger.info(f"Trading will never end: {helper.to_isoformat(end_time)}")
    try:
        for trigger in provider.receive(granular):
            if time.time() * 1000 > end_time:
                shutdown.set()
            if shutdown.is_set():
                break
            logger.info(f"Trigger Datetime: {helper.to_isoformat(trigger['data']['current_time'])}")

            strategy.invoke()
    finally:
        logger.info("Trading process terminated gracefully.")
