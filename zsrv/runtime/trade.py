from solvexity.trader.config import ConfigLoader
import solvexity.helper.logging as logging
from solvexity.helper.shutdown import Shutdown
import solvexity.helper as helper
import json

logger = logging.getLogger()

def trading_runtime(config_loader: ConfigLoader, shutdown: Shutdown, trade_service: str, feed_service: str, granular: str):
    strategy = config_loader["strategies"][trade_service]
    provider = config_loader["feeds"][feed_service]
    shutdown.register(lambda signum: provider.close())
    shutdown.register(lambda signum: strategy.close())
    try:
        for trigger in provider.receive(granular):
            if shutdown.is_set():
                break
            logger.info(f"Trigger Datetime: {helper.to_isoformat(trigger['data']['current_time'])}")

            strategy.invoke()
    finally:
        logger.info("Trading process terminated gracefully.")
