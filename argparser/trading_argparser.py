import argparse
import helper
import helper.logging as logging
import threading
import signal
import traceback
from service import ServiceFactory
from trader.data.provider import DataProviderFactory
from trader.context import ContextFactory
from trader.signal import SignalFactory, SignalType
from trader.policy import PolicyFactory
from trader.strategy import StrategyFactory

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

def main(services_config: dict, 
         data_config:dict, 
         context_config: dict, 
         signal_config: dict,
         policy_config: dict,
         strategy_config: dict):
    services = ServiceFactory(services_config)
    contexts = ContextFactory(services, context_config)
    signals = SignalFactory(contexts, signal_config)
    providers = DataProviderFactory(services, data_config)
    policies = PolicyFactory(contexts, policy_config)
    strategies = StrategyFactory(signals, policies, strategy_config)

    # Retrieve a strategy
    pythagoras_btc = strategies["pythagoras_btc"]
    provider = providers["historical_provider"]

    signal.signal(signal.SIGINT, lambda signum, frame: provider.stop())
    signal.signal(signal.SIGTERM, lambda signum, frame: provider.stop())

    try:
        for _ in provider.receive():
            if shutdown_event.is_set():
                break
            pythagoras_btc.invoke()
    finally:
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
        main(config["services"], 
             config["data"], 
             config["contexts"], 
             config["signals"],
             config["policies"],
             config["strategies"])
    except Exception as e:
        full_traceback = traceback.format_exc()
        logger.error(f"Error invoking strategy: {e}\n{full_traceback}")
