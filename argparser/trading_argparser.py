import argparse
import helper.utils as utils
import helper.logging as logging
from binance.client import Client


def parse_arguments():
    parser = argparse.ArgumentParser(description="Read configuration and run trading process")
    parser.add_argument(
        "-c", "--config",
        type=str,
        required=True,
        help="Path to the configuration file"
    )
    return parser.parse_args()



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
    binance_client = Client(config["binance"]["api_key"], config["binance"]["api_secret"])
    trades = binance_client.get_aggregate_trades(symbol='BNBBTC')
    logger.info(f"Retrieved {len(trades)} trades")

