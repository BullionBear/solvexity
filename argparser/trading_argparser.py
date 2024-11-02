import argparse
import time
import redis
import helper
import helper.logging as logging
import threading
import signal
import traceback
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

    wait_time = 1  # Start with 1 second
    max_wait_time = 10  # Cap the backoff at 10 seconds
    
    if trading_config["family"] == "pythagoras":
        Strategy = Pythagoras
    else:
        raise ValueError(f"Unknown strategy family: {trading_config['family']}")

    with Strategy(binance_client, trading_config, webook_url) as strategy:
        # while not shutdown_event.is_set():
        while not shutdown_event.is_set():
            current_time = int(time.time() * 1000)
            retro_time = current_time - helper.to_unixtime_interval(granular) * (limit + 10) * 1000
            klines = query_kline(r, symbol, granular, retro_time, current_time)
            
            logger.info(f"num of kline data: {len(klines)}")
            if klines:
                logger.info(f"latest kline data: {klines[-1]}")
                
                try:
                    strategy.invoke(klines)
                    # If invoke succeeds, reset the backoff wait time
                    wait_time = 1
                except Exception as e:
                    full_traceback = traceback.format_exc()
                    logger.error(f"Error invoking strategy: {e}\n{full_traceback}")
                    # Increase wait time exponentially with a cap of 10 seconds
                    wait_time = min(wait_time * 2, max_wait_time)
            
            # Wait with the current backoff time, and allow early exit if shutdown is signaled
            if shutdown_event.wait(wait_time):
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

    try:
        main(binance_client, r, trading_config, notification_config["webhook"])
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
