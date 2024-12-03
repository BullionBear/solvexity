import argparse
import solvexity.helper as helper
import solvexity.helper.logging as logging
import signal
import traceback
import json
from solvexity.trader.config import ConfigLoader

logging.setup_logging()
logger = logging.getLogger("trading")
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
    pythagoras_btc = config_loader["strategies"]["pythagoras_btc"]
    provider = config_loader["feeds"]["online_spot"]
    shutdown.register(lambda signum: provider.close())
    shutdown.register(lambda signum: pythagoras_btc.close())

    try:
        for trigger in provider.receive("1m"):
            if shutdown.is_set():
                break

            logger.info(f"Trigger: {trigger}, type: {type(trigger)}")
            # trigger_message = json.loads(trigger["data"].decode("utf-8"))
            # logger.info(f"Trigger Message: {trigger_message}")
            logger.info(f"Datetime: {helper.to_isoformat(trigger["data"]["current_time"])}")

            pythagoras_btc.invoke()
    finally:
        logger.info("Trading process terminated gracefully.")
        # After some time, check which threads are running)

if __name__ == "__main__":
    args = parse_arguments()
    try:
        config = ConfigLoader.from_file(args.config)
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        raise
    
    logger.info("Configuration loaded successfully")

    try:
        main(config)
    except Exception as e:
        full_traceback = traceback.format_exc()
        logger.error(f"Error invoking strategy: {e}\n{full_traceback}")
