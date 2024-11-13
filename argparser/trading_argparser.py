import argparse
import time
import redis
import helper
import helper.logging as logging
import threading
import signal
import json
import traceback
from binance.client import Client as BinanceClient
from trader.data import query_kline, get_key
from trader.core import LiveTradeContext
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

def main(services_config: dict, trigger_config: dict, context_config: dict, trading_config: dict):
    services = {}
    services["redis"] = redis.Redis(host=services_config["redis"]["host"], port=services_config["redis"]["port"], db=services_config["redis"]["db"])
    services["binance"] = BinanceClient(services_config["binance"]["api_key"], services_config["binance"]["api_secret"])
    services["webhook"] = services_config["webhook"]

    if context_config["mode"] == "live":
        logger.info("Initializing live trading context")
        client = context_config["client"]
        r = context_config["redis"]
        webhook = context_config["webhook"]
        granular = context_config["granular"]
        context = LiveTradeContext(services[client], services[r], services[webhook], granular)
    elif context_config["mode"] == "paper":
        raise NotImplementedError("Paper trading context is not implemented yet")
    else:
        raise ValueError("Unknown context mode")
    
    if trading_config["family"] == "pythagoras":
        Strategy = Pythagoras
    else:
        raise ValueError(f"Unknown strategy family: {trading_config['family']}")
    symbol = trigger_config["symbol"]
    granular = trigger_config["granular"]
    with Strategy(context, trading_config["symbol"], trading_config["limit"], trading_config["meta"]) as strategy:
        # while not shutdown_event.is_set():
        pubsub = r.pubsub()
        key = get_key(symbol, granular)
        pubsub.subscribe(key)
        for msg in pubsub.listen():
            current_time = int(time.time() * 1000)
            message = json.loads(msg)
            logger.info(f"Received message: {message}")
            # retro_time = current_time - helper.to_unixtime_interval(granular) * (limit + 10) * 1000
            # klines = query_kline(r, symbol, granular, retro_time, current_time)
            # 
            # logger.info(f"num of kline data: {len(klines)}")
            # if len(klines) >= limit:
            #     logger.info(f"latest kline data: {klines[-1]}")    
            #     try:
            #         strategy.invoke(klines)
            #     except Exception as e:
            #         full_traceback = traceback.format_exc()
            #         logger.error(f"Error invoking strategy: {e}\n{full_traceback}")
            
            if shutdown_event.is_set():
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

    try:
        main(config["services"], config["trigger"], config["context"], config["trading"])
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
