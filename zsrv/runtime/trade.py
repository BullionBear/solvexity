from trader.config import ConfigLoader
import helper.logging as logging
import signal

logger = logging.getLogger("trade")

def trading_runtime(config_loader: ConfigLoader, trade_service: str, data_service: str):
    try:
        strategy = config_loader["strategies"][trade_service]
        provider = config_loader["feeds"][data_service]
        for _ in provider.receive():
            strategy.invoke()
    finally:
        logger.info("Trading process terminated gracefully.")