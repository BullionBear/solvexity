import argparse
import json
import time
import redis
from binance import ThreadedWebsocketManager
from binance.client import Client as BinanceClient
import utils
import utils.logging as logging
from trading.data import get_key, query_kline, query_latest_kline

logging.setup_logging()
logger = logging.getLogger("data")

MAX_SIZE = 1024

def parse_arguments():
    parser = argparse.ArgumentParser(description="Read configuration and run trading process")
    parser.add_argument(
        "-c", "--config",
        type=str,
        required=True,
        help="Path to the configuration file"
    )
    return parser.parse_args()    


def main(r: redis.Redis, data_config: dict):
    symbol = data_config["symbol"]
    granular = data_config["granular"]
    limit = data_config.get("limit", 1024)
    key = get_key(symbol, granular)
    r.delete(key) # Clear existing data

    twm = ThreadedWebsocketManager(api_key="", api_secret="")
    # start is required to initialise its internal loop
    twm.start()
    
    def handle_socket_message(msg: dict):
        if msg.get('e', '') == 'kline':
            logger.info(f"Kline data: {msg}")
            kline = msg['k']
            score = kline['t']
            latest_kline = query_latest_kline(r, symbol, granular)
            if latest_kline['t'] == score:
                with r.pipeline() as pipe:
                    pipe.zrem(key, json.dumps(latest_kline))
                    pipe.zadd(key, {json.dumps(kline): score})
            else:
                r.zadd(key, {json.dumps(kline): score})
            if r.zcard(key) > MAX_SIZE:
                # Remove oldest elements (those with lowest score) to keep only MAX_SIZE items
                r.zremrangebyrank(key, 0, -MAX_SIZE - 1)
        else:
            logger.error(f"Unknown message type: {msg}")

    twm.start_kline_socket(callback=handle_socket_message, symbol=symbol)
    klines = query_kline(r, symbol, granular, 0, int(time.time() * 1000))
    while not first_kline:
        logger.info("Waiting for kline data...")
        time.sleep(1)
        klines = query_kline(r, symbol, granular, 0, int(time.time() * 1000))
    first_kline = klines[0]
    logger.info(f"First kline data: {first_kline}")
    ts_granular = utils.to_unixtime_interval(granular)
    historical_klines = BinanceClient().get_klines(**{
        "symbol": symbol, 
        "interval": granular, 
        "startTime":first_kline['t'] - ts_granular * limit * 1000 - 1, 
        "endTime": first_kline['t'] -1
        })
    logger.info(f"{historical_klines=}")
    twm.join()




if __name__ == "__main__":
    args = parse_arguments()
    try:
        config = utils.load_config(args.config)
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        raise
    logger.info(f"Start consuming {config["data"]["symbol"]} kline data")
    redis_config = config["redis"]
    r = redis.Redis(host=redis_config["host"], port=redis_config["port"], db=redis_config["db"])
    data_config = config["data"]
    main(r, data_config)

