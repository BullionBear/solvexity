import zmq
import argparse
from dotenv import load_dotenv
import os
import json
from zsrv.zdependency import get_database_client, get_service_config, get_system_config
import helper.logging as logging
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


def start_server(host, port, config_loader):
    """Starts the ZeroMQ server."""
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    address = f"tcp://{host}:{port}"
    socket.bind(address)
    logger.info(f"Server started at {address}")
    
    while True:
        message = socket.recv_string()
        logger.info(f"Received: {message}")
        try:
            data = json.loads(message)
            # Use `config_loader` if needed to process the data
            logger.info(f"Data: {data}")
            socket.send_string(json.dumps({"type": "success", "message": "Data received"}))
        except json.JSONDecodeError:
            logger.error("Invalid JSON received")
            socket.send_string(json.dumps({"type": "error", "message": "Invalid JSON format"}))


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

        # Initialize ConfigLoader
        config_loader = ConfigLoader(system_config)

        # Start the server
        start_server(srv_config["host"], srv_config["port"], config_loader)
    except Exception as e:
        logger.error(f"Error during startup: {e}")
    finally:
        if 'client' in locals():
            client.close()
