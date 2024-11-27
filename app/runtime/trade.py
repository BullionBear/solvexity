from trader.config import ConfigLoader
from helper import Shutdown
import helper.logging as logging
import signal

shutdown = Shutdown(signal.SIGINT, signal.SIGTERM)
logger = logging.getLogger("trade")

def trading_runtime(config_loader: ConfigLoader, trade_service: str, data_service: str):
    try:
        strategy = config_loader["strategies"][trade_service]
        shutdown.register(lambda signum: strategy.stop())
        provider = config_loader["feeds"][data_service]
        shutdown.register(lambda signum: provider.stop())
        for _ in provider.receive():
            if shutdown.is_set():
                break
            strategy.invoke()
    finally:
        logger.info("Trading process terminated gracefully.")