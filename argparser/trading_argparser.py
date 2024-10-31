import argparse
import time
import helper.utils as utils
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

def main(binance_client: BinanceClient, config: dict):
    symbol = config["symbol"]
    granular = config["granular"]
    if config["family"] == "pythagoras":
        tr = Pythagoras()
    while True:
        # Get the latest kline data
        
        # Wait
        time.sleep(1)

if __name__ == "__main__":
    logging.setup_logging()
    logger = logging.getLogger("trading")
    args = parse_arguments()
    try:
        config = utils.load_config(args.config)
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        raise
    logger.info("Configuration loaded successfully")
    binance_config = config["binance"]
    binance_client = BinanceClient(binance_config["api_key"], binance_config["api_secret"])
    trading_config = config["trading"]
    main(binance_client, config)

