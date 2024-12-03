from solvexity.trader.config import ConfigLoader
import solvexity.helper.logging as logging
from solvexity.helper.shutdown import Shutdown
import solvexity.helper as helper
import json

logger = logging.getLogger("trading")

def trading_runtime(config_loader: ConfigLoader, shutdown: Shutdown, trade_service: str, feed_service: str, granular: str):
    try:
        
        strategy = config_loader["strategies"][trade_service]
        shutdown.register(lambda signum: strategy.close())
        provider = config_loader["feeds"][feed_service]
        shutdown.register(lambda signum: provider.close())
        for trigger in provider.receive(granular):
            if shutdown.is_set():
                break
            trigger_message = json.loads(trigger)
            logger.info(f"Trigger: {helper.to_isoformat(trigger_message["data"]["current_time"])}")
            strategy.invoke()
    finally:
        logger.info("Trading process terminated gracefully.")