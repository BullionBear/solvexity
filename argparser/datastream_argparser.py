import sys
import argparse
import time
import signal
import threading
import redis
from binance import ThreadedWebsocketManager
from binance.client import Client as BinanceClient
import helper
import helper.logging as logging
from trader.data import (
    get_key, query_kline, query_latest_kline, batch_insert_klines,
    KLine
)

logging.setup_logging()
logger = logging.getLogger("data")

MAX_SIZE = 128
shutdown_event = threading.Event()  # Event for managing shutdown

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

def main(r: redis.Redis, data_config: dict):
    symbol = data_config["symbol"]
    granular = data_config["granular"]
    limit = data_config["limit"]
    logger.info(f"Start consuming {symbol} kline data, granular: {granular}, limit: {limit}")
    key = get_key(symbol, granular)
    r.delete(key)  # Clear existing data

    twm = ThreadedWebsocketManager(api_key="", api_secret="")
    twm.start()  # Start the WebSocket manager

    def handle_socket_message(msg: dict):
        if shutdown_event.is_set():
            return  # Stop processing if shutdown is triggered
        if msg.get('e', '') == 'kline':
            kline = KLine.from_ws(msg['k'])
            score = kline.open_time
            latest_kline = query_latest_kline(r, symbol, granular)
            if latest_kline is not None and latest_kline.open_time == score:
                logger.info(f"Received duplicate kline data: {kline}")
                with r.pipeline() as pipe:
                    pipe.zrem(key, latest_kline.model_dump_json())
                    pipe.zadd(key, {kline.model_dump_json(): score})
                    pipe.execute()
            else:
                logger.info(f"New kline data received: {kline}")
                r.zadd(key, {kline.model_dump_json(): score})
            if r.zcard(key) > MAX_SIZE:
                # Remove oldest elements (those with lowest score) to keep only MAX_SIZE items
                logger.info(f"Removing oldest kline data to keep only {MAX_SIZE} items")
                r.zremrangebyrank(key, 0, -MAX_SIZE - 1)
        else:
            logger.error(f"Unknown message type: {msg}")

    # Register WebSocket stream for kline data
    twm.start_kline_socket(callback=handle_socket_message, symbol=symbol, interval=granular)
    i = 0
    while not shutdown_event.is_set():
        logger.info("Waiting for kline data...")
        time.sleep(1)
        klines = query_kline(r, symbol, granular, 0, int(time.time() * 1000))
        if len(klines) > 0:
            break
        i += 1
        if i == 9:
            logger.error("No kline data received after 10 seconds. Exiting...")
            twm.stop()
            sys.exit(1)
    first_kline = klines[0]
    logger.info(f"First kline data: {first_kline}")
    ts_granular = helper.to_unixtime_interval(granular)
    historical_klines = BinanceClient().get_klines(**{
        "symbol": symbol, 
        "interval": granular, 
        "startTime": first_kline.open_time - ts_granular * limit * 1000 - 1, 
        "endTime": first_kline.open_time -1
    })
    logger.info(f"Fetch {len(historical_klines)} historical klines")
    klines = [KLine.from_rest(kline, granular) for kline in historical_klines]
    batch_insert_klines(r, key, klines)

    # Wait for shutdown event to stop the WebSocket
    shutdown_event.wait()
    logger.info("Shutting down WebSocket manager...")
    twm.stop()  # Stop the WebSocket manager

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
    
    redis_config = config["redis"]
    r = redis.Redis(host=redis_config["host"], port=redis_config["port"], db=redis_config["db"])
    data_config = config["data"]
    
    main(r, data_config)
