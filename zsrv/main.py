import zmq
import argparse
from dotenv import load_dotenv
import os
import json
from zsrv.zdependency import get_database_client, get_service_config, get_system_config
import helper.logging as logging
from helper import Shutdown
import signal
import threading
from .dispatcher import CommandHandler, Command
from trader.config import ConfigLoader

# Load environment variables from .env
load_dotenv()

logging.setup_logging()
logger = logging.getLogger("service")

SOLVEXITY_MONGO_URI = os.getenv("SOLVEXITY_MONGO_URI")


def parse_arguments():
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(description="ZeroMQ Server Configuration")
    parser.add_argument("-s", "--service", type=str, required=True, help="Service name")
    return parser.parse_args()


def start_server(host, port, config_loader, shutdown):
    """Starts the ZeroMQ server."""
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    address = f"tcp://{host}:{port}"
    socket.bind(address)
    socket.RCVTIMEO = 1000  # Set timeout to 1000 milliseconds (1 second)
    logger.info(f"Server started at {address}")

    handler = CommandHandler(config_loader)
    while not shutdown.is_set():
        try:
            # Attempt to receive a message with a timeout
            message = socket.recv_string()
            logger.info(f"Received: {message}")
            try:
                response = Command.from_string(message).execute(handler)
                socket.send_string(json.dumps({"type": "success", "message": "Data received"}))
            except json.JSONDecodeError:
                logger.error("Invalid JSON received")
                socket.send_string(json.dumps({"type": "error", "message": "Invalid JSON format"}))
        except zmq.Again:
            # This exception occurs when a timeout happens
            logger.debug("No message received (timeout).")
            continue
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            break


if __name__ == "__main__":
    args = parse_arguments()
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
        thread = None
        if srv_config["runtime"] == "feed":
            # Start the feed runtime
            from zsrv.runtime.feed import feed_runtime
            feed_args = srv_config["arguments"]
            thread = threading.Thread(target=feed_runtime, args=(config_loader, shutdown, feed_args["feed"]))
        elif srv_config["runtime"] == "trade":
            # Start the trade runtime
            from zsrv.runtime.trade import trading_runtime
            trade_args = srv_config["arguments"]
            thread = threading.Thread(target=trading_runtime, args=(config_loader, shutdown, trade_args["strategy"], trade_args["feed"]))
        else:
            logger.error("Invalid runtime specified")
            raise ValueError("Invalid runtime specified")
        thread.start()
        # Start the server
        start_server(srv_config["host"], srv_config["port"], config_loader, shutdown)
    except Exception as e:
        logger.error(f"Error during startup: {e}")
    finally:
        if 'thread' in locals():
            thread.join()
        if 'client' in locals():
            client.close()
