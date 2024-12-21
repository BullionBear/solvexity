import zmq
import argparse
from dotenv import load_dotenv
import os
from zsrv.zdependency import get_database_client, get_service_config, get_system_config
import solvexity.helper.logging as logging
from solvexity.helper import Shutdown
import signal
import threading
from zsrv.dispatcher.command import CommandHandler, Command
from solvexity.trader.config import ConfigLoader

# Load environment variables from .env
load_dotenv()

logging.setup_logging()
logger = logging.getLogger()

SOLVEXITY_MONGO_URI = os.getenv("SOLVEXITY_MONGO_URI")


def parse_arguments():
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(description="ZeroMQ Server Configuration")
    parser.add_argument("-s", "--service", type=str, required=True, help="Service name")
    return parser.parse_args()


def start_server(host: str, port: int, handler: CommandHandler, shutdown: Shutdown):
    """Starts the ZeroMQ server."""
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    address = f"tcp://{host}:{port}"
    socket.bind(address)
    socket.RCVTIMEO = 1000  # Set timeout to 1000 milliseconds (1 second)
    logger.info(f"Server started at {address}")
    while not shutdown.is_set():
        try:
            # Attempt to receive a message with a timeout
            message = socket.recv_json()
            logger.info(f"Received: {message}")
            response = Command.from_dict(message).execute(handler)
            socket.send_json(response.to_dict())
        except zmq.Again:
            # This exception occurs when a timeout happens
            logger.debug("No message received (timeout).")
            continue
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            break
    logger.info("Shutting down server...")


if __name__ == "__main__":
    args = parse_arguments()
    logging.setup_logging(args.service)
    logger.info("Starting up...")

    try:
        client = get_database_client(SOLVEXITY_MONGO_URI)
        db = client["solvexity"]
        # Fetch configurations
        srv_config = get_service_config(db, args.service)
        system_name = srv_config["ref"]
        system_config = get_system_config(db, system_name)
        shutdown = Shutdown(signal.SIGINT, signal.SIGTERM)
        # Initialize ConfigLoader
        config_loader = ConfigLoader(system_config)
        handler = None
        if srv_config["runtime"] == "feed":
            # Start the feed runtime
            from zsrv.runtime.feed import feed_runtime
            feed_args = srv_config["arguments"]
            thread = threading.Thread(target=feed_runtime, args=(config_loader, 
                                                                 shutdown, 
                                                                 feed_args["feed"]))
            from zsrv.dispatcher.handler.feed_handler import FeedHandler
            handler = FeedHandler(config_loader)
        elif srv_config["runtime"] == "trade":
            # Start the trade runtime
            from zsrv.runtime.trade import trading_runtime
            trade_args = srv_config["arguments"]
            thread = threading.Thread(target=trading_runtime, args=(config_loader, 
                                                                    shutdown, 
                                                                    trade_args["strategy"], 
                                                                    trade_args["feed"], 
                                                                    trade_args["granular"], 
                                                                    trade_args["n_live_granular"]))
            from zsrv.dispatcher.handler.trade_handler import TradeHandler
            handler = TradeHandler(config_loader)
        else:
            logger.error("Invalid runtime specified")
            raise ValueError("Invalid runtime specified")
        thread.start()
        # Start the server
        start_server("0.0.0.0", srv_config["port"], handler, shutdown)
    except Exception as e:
        logger.error(f"Error starting up: {e}", exc_info=True)
    finally:
        if 'thread' in locals() and thread.is_alive():
            thread.join()
        if 'client' in locals():
            client.close()
