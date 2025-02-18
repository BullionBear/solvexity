import json5 as json
import logging
import random
import string
from typing import Any
from decimal import Decimal, ROUND_DOWN
from binance.client import Client as BinanceClient
from datetime import datetime, timezone
from functools import lru_cache

logger = logging.get_logger()

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
    except Exception as e:
        logger.error(f"Error loading configuration: {e}", exc_info=True)
        raise 

def to_unixtime_interval(interval_str: str) -> int:
    # Define mappings for time units to seconds
    unit_mappings = {
        's': 1,         # seconds
        'm': 60,        # minutes
        'h': 3600,      # hours
        'd': 86400,     # days
    }
    
    # Extract the numeric part and the unit part
    try:
        value = int(interval_str[:-1])  # Get the number (e.g., 5 from '5m')
        unit = interval_str[-1]         # Get the unit character (e.g., 'm' from '5m')
        
        if unit in unit_mappings:
            return value * unit_mappings[unit]
        else:
            raise ValueError("Invalid time unit. Use 's', 'm', 'h', or 'd'.")
    
    except (ValueError, IndexError):
        raise ValueError("Invalid interval format. Please use formats like '1s', '5m', '1h', '5d'.")

def to_isoformat(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc).isoformat()

def generate_random_id(length=8):
    characters = string.ascii_letters + string.digits
    random_id = ''.join(random.choice(characters) for _ in range(length))
    return random_id

def symbol_filter(symbol: str, size: Decimal, price: Decimal) -> tuple[Decimal, Decimal]:
    symbol_info = _get_symbol_info(symbol)
    for _filter in symbol_info['filters']:
        if _filter['filterType'] == 'PRICE_FILTER':
            tick_size = Decimal(_filter['tickSize']).normalize()
            price = price.quantize(tick_size, rounding=ROUND_DOWN)
        elif _filter['filterType'] == 'LOT_SIZE':
            lot_size = Decimal(_filter['stepSize']).normalize()
            size = size.quantize(lot_size, rounding=ROUND_DOWN)
    return size, price

def to_content(obj: dict[str, Any]) -> str:
    return "\n".join([f"**{k}**: {v}" for k, v in obj.items()])
    

@lru_cache(maxsize=128)  # Set the cache size to 128 entries (or adjust as needed)
def _get_symbol_info(symbol):
    client = BinanceClient()
    symbol_info = client.get_symbol_info(symbol)
    return symbol_info
