import argparse
import signal
import solvexity.helper as helper
import solvexity.helper.logging as logging
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
    provider = config_loader["data"]["historical_provider"]
    shutdown.register(lambda signum: provider.stop())
    shutdown.register(lambda signum: pythagoras_btc.stop())

    try:
        for _ in provider.send():
            if shutdown.is_set():
                break
            _ = provider.receive()
            pythagoras_btc.invoke()
    finally:
        logger.info("Trading process terminated gracefully.")
    


if __name__ == "__main__":
    args = parse_arguments()
    try:
        config = ConfigLoader.from_file(args.config)
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        raise ValueError(e)
    
    main(config)
