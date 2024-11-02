import argparse
import time
import redis
import helper
import helper.logging as logging
import threading
import signal
from binance.client import Client as BinanceClient
from trader.data import query_kline
from trader.strategy import Pythagoras

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

def handle_shutdown_signal(signum, frame):
    logger.info("Shutdown signal received. Shutting down gracefully...")
    shutdown_event.set()

def main(binance_client: BinanceClient, r: redis.Redis, trading_config: dict, webook_url: str):
    symbol = trading_config["symbol"]
    granular = trading_config["granular"]
    limit = trading_config["limit"]
    
    if trading_config["family"] == "pythagoras":
        Strategy = Pythagoras
    else:
        raise ValueError(f"Unknown strategy family: {trading_config['family']}")

    with Strategy(binance_client, trading_config, webook_url) as strategy:
        while not shutdown_event.is_set():
            # Get the latest kline data
            current_time = int(time.time() * 1000)
            retro_time = current_time - helper.to_unixtime_interval(granular) * (limit + 10) * 1000
            klines = query_kline(r, symbol, granular, retro_time, current_time)
            
            logger.info(f"num of kline data: {len(klines)}")
            if klines:
                logger.info(f"latest kline data: {klines[-1]}")
                strategy.invoke(klines)
            
            # Wait, but allow early exit if shutdown is signaled
            if shutdown_event.wait(1):
                break

    logger.info("Trading process terminated gracefully.")

if __name__ == "__main__":
    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, handle_shutdown_signal)
    signal.signal(signal.SIGTERM, handle_shutdown_signal)
    
    args = parse_arguments()
    try:
        config = helper.load_config(args.config)
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        raise
    
    logger.info("Configuration loaded successfully")
    binance_config = config["binance"]
    binance_client = BinanceClient(binance_config["api_key"], binance_config["api_secret"])
    redis_config = config["redis"] 
    r = redis.Redis(host=redis_config["host"], port=redis_config["port"], db=redis_config["db"])
    trading_config = config["trading"]
    notification_config = config["notification"]

    main(binance_client, r, trading_config, notification_config["webhook"])
