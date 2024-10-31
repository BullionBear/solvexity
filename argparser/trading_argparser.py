import argparse
import utils.utils as utils
import utils.logging as logging

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

