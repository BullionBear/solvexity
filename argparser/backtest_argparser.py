import argparse
import time
import helper
import helper.logging as logging
import threading
import signal
from sqlalchemy import create_engine


logging.setup_logging()
logger = logging.getLogger("trading")
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

def handle_shutdown(signum, frame):
    """Signal handler for graceful shutdown."""
    logger.info("Shutdown signal received, stopping...")
    shutdown_event.set()  # Trigger shutdown event to stop main loop

def main(data_config: dict, trading_config: dict):
    symbol = data_config["symbol"]
    granular = data_config["granular"]
    granular_ts = helper.to_unixtime_interval(granular) * 1000
    limit = data_config["limit"]
    start = data_config["start"] // granular_ts * granular_ts
    end = data_config["end"] // granular_ts * granular_ts
    db_url = data_config["url"]
    db = create_engine(db_url)


if __name__ == "__main__":
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    args = parse_arguments()
    try:
        config = helper.load_config(args.config)
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        raise    
    logger.info(f"Start consuming {config['data']['symbol']} kline data")
    
    data_config = config["data"]
    trading_config = config["trading"]
    
    main(data_config, trading_config)


