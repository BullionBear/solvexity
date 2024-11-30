from solvexity.trader.config import ConfigLoader
import solvexity.helper.logging as logging
from solvexity.helper.shutdown import Shutdown

logger = logging.getLogger("trading")

def trading_runtime(config_loader: ConfigLoader, shutdown: Shutdown, trade_service: str, feed_service: str):
    try:
        strategy = config_loader["strategies"][trade_service]
        shutdown.register(lambda signum: strategy.close())
        provider = config_loader["feeds"][feed_service]
        shutdown.register(lambda signum: provider.close())
        for _ in provider.receive():
            strategy.invoke()
    finally:
        logger.info("Trading process terminated gracefully.")