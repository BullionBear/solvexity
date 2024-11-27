from trader.config import ConfigLoader
from helper import Shutdown
import helper.logging as logging
import signal

shutdown = Shutdown(signal.SIGINT, signal.SIGTERM)
logger = logging.getLogger("trade")

def trading_runtime(config_loader: ConfigLoader, trade_service: str, data_service: str):
    # Retrieve a strategy
    strategy = config_loader["strategies"][trade_service]
    provider = config_loader["data"][data_service]

    try:
        for _ in provider.receive():
            if shutdown.is_set():
                break
            strategy.invoke()
    finally:
        provider.stop()
        strategy.stop()
        logger.info("Trading process terminated gracefully.")