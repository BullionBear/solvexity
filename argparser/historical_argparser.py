import argparse
import solvexity.helper
import solvexity.helper.logging as logging
import threading
import signal
import traceback
from solvexity.trader.config import ConfigLoader

logging.setup_logging()
logger = logging.getLogger("feed")
shutdown_event = threading.Event()

def parse_arguments():
    parser = argparse.ArgumentParser(description="Read configuration and run trading process")
    parser.add_argument(
        "-c", "--config",
        type=str,
        required=True,
        help="Path to the configuration file"
    )
    return parser.parse_args()

def handle_shutdown_signal(signum, frame):
    logger.info("Shutdown signal received. Shutting down gracefully...")
    shutdown_event.set()

def main(config_loader: ConfigLoader):
    provider = config_loader["feeds"]["offline_btc_easy"]

    # Start provider in a controlled loop
    try:
        for data in provider.send():
            if shutdown_event.is_set():
                break
            logger.info(f"Publish kline data: {data}")
    finally:
        provider.close()

    logger.info("Trading process terminated gracefully.")

if __name__ == "__main__":
    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, handle_shutdown_signal)
    signal.signal(signal.SIGTERM, handle_shutdown_signal)
    
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
