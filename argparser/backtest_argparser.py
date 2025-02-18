import argparse
import signal
import solvexity.helper as helper
import solvexity.helper.logging as logging
from solvexity.trader.config import ConfigLoader
import json

logging.setup_logging()
logger = logging.get_logger()
shutdown = helper.Shutdown(signal.SIGINT, signal.SIGTERM)

def parse_arguments():
    parser = argparse.ArgumentParser(description="Read configuration and run trading process")
    parser.add_argument(
        "-c", "--config",
        type=str,
        required=True,
        help="Path to the configuration file"
    )
    return parser.parse_args()


def main(config_loader: ConfigLoader):
    # Retrieve a strategy
    shutdown = helper.Shutdown(signal.SIGINT, signal.SIGTERM)
    provider = config_loader["feeds"]["offline_spot"]
    shutdown.register(lambda signum: provider.close())
    pythagoras_btc = config_loader["strategies"]["pythagoras_btc"]
    shutdown.register(lambda signum: pythagoras_btc.close())
    try:
        for tigger in provider.send():
            if shutdown.is_set():
                break
            trigger_message = json.loads(tigger)
            # logger.info(f"Trigger: {trigger_message}")
            if trigger_message["data"]["granular"] == "1h":
                # Fetch only one message
                try:
                    recv_message = next(provider.receive("1h"))
                    logger.info(f"Received: {recv_message}")
                    pythagoras_btc.invoke()
                except StopIteration:
                    logger.warning("No message received for 1h granular.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
    finally:
        shutdown.trigger_callbacks()  # Ensure all callbacks are executed
        logger.info("Trading process terminated gracefully.")


if __name__ == "__main__":
    args = parse_arguments()
    try:
        config = ConfigLoader.from_file(args.config)
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        raise ValueError(e)
    
    main(config)
