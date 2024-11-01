import argparse
import time
import redis
import helper
import helper.logging as logging
from binance.client import Client as BinanceClient
from trader.data import query_kline
from trader.strategy import Pythagoras



def parse_arguments():
    parser = argparse.ArgumentParser(description="Read configuration and run trading process")
    parser.add_argument(
        "-c", "--config",
        type=str,
        required=True,
        help="Path to the configuration file"
    )
    return parser.parse_args()

def main(binance_client: BinanceClient, r: redis.Redis, trading_config: dict):
    symbol = trading_config["symbol"]
    granular = trading_config["granular"]
    if trading_config["family"] == "pythagoras":
        tr = Pythagoras()
    while True:
        # Get the latest kline data
        current_time = int(time.time() * 1000)
        klines = query_kline(r, symbol, granular, current_time - helper.to_unixtime_interval(granular) * 90, current_time)
        logger.info(f"num of kline data: {len(klines)}")
        logger.info(f"latest kline data: {klines[-1]}")
        # Wait
        time.sleep(1)

if __name__ == "__main__":
    logging.setup_logging()
    logger = logging.getLogger("trading")
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
    r = redis.Redis(host=redis_config["host"], port=redis_config["port"], db=redis_config)
    trading_config = config["trading"]

    main(binance_client, r, trading_config)

