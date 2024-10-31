import argparse
import json
import redis
from binance import ThreadedWebsocketManager
import utils.utils as utils
import utils.logging as logging
from trading.data import get_key

logging.setup_logging()
logger = logging.getLogger("data")

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

    twm = ThreadedWebsocketManager(api_key="", api_secret="")
    # start is required to initialise its internal loop
    twm.start()
    key = get_key(symbol, granular)
    def handle_socket_message(msg: dict):
        if msg.get('e', '') == 'kline':
            logger.info(f"Kline data: {msg}")
            kline = msg['k']
            score = kline['t']
            r.zadd(key, {json.dumps(kline): score})
            if r.zcard(key) > limit:
                # Remove oldest elements (those with lowest score) to keep only MAX_SIZE items
                r.zremrangebyrank(key, 0, -limit - 1)
        else:
            logger.error(f"Unknown message type: {msg}")

    twm.start_kline_socket(callback=handle_socket_message, symbol=symbol)

    # multiple sockets can be started
    # twm.start_depth_socket(callback=handle_socket_message, symbol=symbol)

    # or a multiplex socket can be started like this
    # see Binance docs for stream names
    # streams = ['bnbbtc@miniTicker', 'bnbbtc@bookTicker']
    # twm.start_multiplex_socket(callback=handle_socket_message, streams=streams)
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

