import argparse
import helper
import helper.logging as logging
import threading
import signal
import json
import time
import traceback
from service import ServiceFactory
from trader.data import get_key
from trader.data.provider import DataProviderFactory
from trader.context import ContextFactory
from trader.signal import SignalFactory

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

def heartbeat(redis, interval):
    while not shutdown_event.is_set():
        message = json.dumps({"type": "ping", "timestamp": int(time.time()) * 1000})
        redis.publish("heartbeat", message)
        time.sleep(interval)  # Send a ping every `interval` seconds
    message = json.dumps({"type": "ping", "timestamp": int(time.time()) * 1000})
    redis.publish("heartbeat", message)
    logger.info("Heartbeat thread terminated.")

def main(services_config: dict, data_config:dict, context_config: dict, signal_config: dict):
    services = ServiceFactory(services_config)
    contexts = ContextFactory(services, context_config)
    signals = SignalFactory(contexts, signal_config)
    providers = DataProviderFactory(services, data_config)

    provider = providers["realtime_provider"]

    # Start provider in a controlled loop
    try:
        for data in provider:
            if shutdown_event.is_set():
                break
            logger.info(f"Publish kline data: {data}")
    finally:
        provider.stop()

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
        main(config["services"], config["data"], config["contexts"], config["signals"])
    except Exception as e:
        full_traceback = traceback.format_exc()
        logger.error(f"Error invoking strategy: {e}\n{full_traceback}")