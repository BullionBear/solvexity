import argparse
import signal
import threading
import helper
import helper.logging as logging
import time
from trader.data.provider import HistoricalProvider
from service import ServiceFactory

logging.setup_logging()
logger = logging.getLogger("data")
shutdown_event = threading.Event()

def parse_arguments():
    parser = argparse.ArgumentParser(description="Read configuration and run playback process")
    parser.add_argument(
        "-c", "--config",
        type=str,
        required=True,
        help="Path to the configuration file"
    )
    return parser.parse_args()

def handle_shutdown(signum, frame):
    """Signal handler for graceful shutdown."""
    logger.info("Shutdown signal received, stopping...")
    shutdown_event.set()  # Trigger shutdown event to stop main loop


def main(service_config: dict, trigger_config: dict, data_config: dict):
    service = ServiceFactory(service_config)
    if data_config["provider"] == "history":
        r = data_config["redis"]
        sql = data_config["sql_engine"]
        provider = HistoricalProvider(
            service[r], service[sql], data_config["symbol"],
            data_config["granular"], data_config["start"], data_config["end"],
            data_config["limit"]
        )
    else:
        raise ValueError(f"Unknown data provider: {data_config['provider']}")
    signal.signal(signal.SIGINT, lambda signum, frame: provider.stop())
    signal.signal(signal.SIGTERM, lambda signum, frame: provider.stop())
    sleep_time = trigger_config["sleep"] / 1000
    for kline in provider:
        if shutdown_event.is_set():
            break
        logger.info(f"Publish kline data: {kline}")
        time.sleep(sleep_time)
    


if __name__ == "__main__":
    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    args = parse_arguments()
    try:
        config = helper.load_config(args.config)
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        raise    
    logger.info("Configuration loaded successfully")

    try:
        main(config["services"], config["trigger"], config["data"])
    except Exception as e:
        logger.error(f"Unexpected error: {e}")