import argparse
import helper
import helper.logging as logging
import threading
import signal
import traceback
from service import ServiceFactory
from trader.config import ConfigLoader

logging.setup_logging()
logger = logging.getLogger("trading")
shutdown = helper.Shutdown(signal.SIGINT, signal.SIGTERM)

def parse_arguments():
    parser = argparse.ArgumentParser(description="Read configuration and run trading process")
    parser.add_argument(
        "-c", "--config",
        type=str,
        required=True,
        help="Path to the configuration file"
    )
    return parser.parse_args()


def main(config_loader: ConfigLoader):
    # Retrieve a strategy
    pythagoras_btc = config_loader["strategies"]["pythagoras_btc"]
    provider = config_loader["data"]["historical_provider"]
    shutdown.register(lambda signum: provider.stop())
    shutdown.register(lambda signum: pythagoras_btc.stop())

    try:
        for _ in provider.receive():
            if shutdown.is_set():
                break
            pythagoras_btc.invoke()
    finally:
        logger.info("Trading process terminated gracefully.")



if __name__ == "__main__":
    args = parse_arguments()
    try:
        config = ConfigLoader.from_file(args.config)
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        raise
    
    logger.info("Configuration loaded successfully")

    try:
        main(config)
    except Exception as e:
        full_traceback = traceback.format_exc()
        logger.error(f"Error invoking strategy: {e}\n{full_traceback}")
