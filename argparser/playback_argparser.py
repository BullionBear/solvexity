import sys
import argparse
import time
import signal
import threading
import redis
from datetime import datetime, timezone
from pytz import utc
from binance.client import Client as BinanceClient
import helper
import helper.logging as logging
from trader.data import (
    get_key, get_engine, get_klines,
    KLine
)

logging.setup_logging()
logger = logging.getLogger("data")


MAX_SIZE = 65536
shutdown_event = threading.Event()  # Event for managing shutdown


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


def main(r: redis.Redis, data_config: dict):
    symbol = data_config["symbol"]
    granular = data_config["granular"]
    granular_ts = helper.to_unixtime_interval(granular) * 1000
    key = get_key(symbol, granular)
    r.delete(key)  # Clear existing data
    # limit = data_config["limit"]
    start = data_config["start"] // granular_ts * granular_ts
    end = data_config["end"] // granular_ts * granular_ts
    db_url = data_config["url"]
    db = get_engine(db_url)

    start_dt = datetime.fromtimestamp(start // 1000, tz=timezone.utc)
    end_dt = datetime.fromtimestamp(end // 1000, tz=timezone.utc)
    logger.info(f"Start consuming {symbol} kline data, granular: {granular} from {start_dt.strftime('%Y-%m-%d %H:%M:%S')} to {end_dt.strftime('%Y-%m-%d %H:%M:%S')}")

    current = start
    while current < end:
        next_day = min(current + 86400 * 1000, end)  # 86400 seconds in a day, multiplied by 1000 for milliseconds
        res = get_klines(db, symbol, granular, current, next_day)
        logger.info(f"Retrieved {len(res)} klines from {datetime.fromtimestamp(current // 1000, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} "
                    f"to {datetime.fromtimestamp(next_day // 1000, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}")
        # res.to_csv(f"{symbol}_{granular}_{current}_{next_day}.csv", index=False)
        current = next_day  # Move to the next day
        if shutdown_event.is_set():
            break
    




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
    logger.info(f"Start consuming {config['data']['symbol']} kline data")

    redis_config = config["redis"]
    r = redis.Redis(host=redis_config["host"], port=redis_config["port"], db=redis_config["db"])
    data_config = config["data"]
    main(r, data_config)