import logging
import logging.config
import json
import redis

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter to format logs in JSON format."""
    def format(self, record):
        log_record = {
            "time": self.formatTime(record),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "line": record.lineno,
            "module": record.module,
            "process_id": record.process,
            "file_path": record.pathname,
        }
        return json.dumps(log_record)

class ColorFormatter(logging.Formatter):
    """Custom formatter to add color to log levels in console output."""
    COLOR_CODES = {
        "DEBUG": "\033[37m",  # White
        "INFO": "\033[32m",   # Green
        "WARNING": "\033[33m", # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[1;31m", # Bold Red
    }
    RESET_CODE = "\033[0m"

    def format(self, record):
        # Apply color to the log level
        color = self.COLOR_CODES.get(record.levelname, self.RESET_CODE)
        record.levelname = f"{color}{record.levelname}{self.RESET_CODE}"
        return super().format(record)


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter to format logs in JSON format."""

    def format(self, record):
        # Convert the log record to a dictionary
        log_record = {
            "time": self.formatTime(record),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "line": record.lineno,
            "module": record.module,
            "process_id": record.process,  # Add process ID
            "file_path": record.pathname,  # Add file path
        }
        return json.dumps(log_record)  # Convert the dictionary to a JSON string
    
class RedisPubSubHandler(logging.Handler):
    """Custom handler to publish logs to a Redis PubSub channel."""
    def __init__(self, redis_host='localhost', redis_port=6379, channel='log_channel'):
        super().__init__()
        self.redis_client = redis.StrictRedis(host=redis_host, port=redis_port, decode_responses=True)
        self.channel = channel

    def emit(self, record):
        try:
            # Format the log record using the assigned formatter
            message = self.format(record)
            # Publish the message to the Redis channel
            self.redis_client.publish(self.channel, message)
        except Exception as e:
            print(f"Failed to publish log to Redis: {e}")

# Define a centralized logging configuration with JSON and readable formatters
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'readable': {
            'format': '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] - %(message)s',
        },
        'json': {
            '()': JSONFormatter,  # Use the custom JSON formatter
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'readable',  # Human-readable format for console
            'stream': 'ext://sys.stdout',
        },
        'redis': {
            '()': RedisPubSubHandler,  # Use the custom Redis handler
            'level': 'INFO',
            'formatter': 'json',
            'redis_host': 'localhost',
            'redis_port': 6379,
            'channel': 'log_channel',
        },
    },
    'loggers': {
        '': {  # Root logger
            'level': 'INFO',
            'handlers': ['console', 'redis'],  # Add Redis handler here
        },
        'trading': {
            'level': 'INFO',
            'handlers': ['console', 'redis'],  # Add Redis handler here
            'propagate': False,
        },
        'feed': {
            'level': 'INFO',
            'handlers': ['console', 'redis'],  # Add Redis handler here
            'propagate': False,
        }
    }
}

def setup_logging():
    """Sets up logging based on the configuration."""
    logging.config.dictConfig(LOGGING_CONFIG)

def setup_logging():
    """
    Sets up logging based on the configuration.
    """
    logging.config.dictConfig(LOGGING_CONFIG)

def getLogger(name=None):
    """
    Returns a logger instance with the specified name.
    """
    return logging.getLogger(name)
