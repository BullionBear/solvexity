import json
import logging

logger = logging.getLogger()

def load_config(file_path):
    try:
        logger.info(f"Loading configuration from {file_path}")
        with open(file_path, 'r') as f:
            config = json.load(f)
        logger.info("Configuration loaded successfully")
        return config
    except FileNotFoundError:
        logger.error(f"Configuration file '{file_path}' not found.")
        raise
    except json.JSONDecodeError:
        logger.error(f"Configuration file '{file_path}' is not a valid JSON.")
        raise