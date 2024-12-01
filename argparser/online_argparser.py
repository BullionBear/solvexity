import argparse
import solvexity.helper.logging as logging
from solvexity.helper import Shutdown, to_isoformat
import signal
import traceback
import json
from solvexity.trader.config import ConfigLoader


logging.setup_logging()
logger = logging.getLogger("feed")

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

def main(config_loader: ConfigLoader):
    shutdown = Shutdown(signal.SIGINT, signal.SIGTERM)
    provider = config_loader["feeds"]["offline_spot"]
    shutdown.register(lambda frame: provider.close())
    # Start provider in a controlled loop
    try:
        for trigger in provider.send():
            trigger_message = json.loads(trigger)
            logger.info(f"Trigger: {trigger_message}")
            logger.info(f"Datetime: {to_isoformat(trigger_message["data"]["current_time"])}")

    finally:
        shutdown.set()

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
