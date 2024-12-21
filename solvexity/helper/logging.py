import logging
import logging.config
import json
import redis
import sys
import uuid
import traceback

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter to format logs in JSON format."""
    def __init__(self, session: str = None):
        super().__init__()
        self.session = session if session else uuid.uuid4().hex

    def format(self, record):
        log_record = {
            "time": self.formatTime(record),
            "session": self.session,
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "line": record.lineno,
            "module": record.module,
            "process_id": record.process,
            "file_path": record.pathname,
        }
        if record.exc_info:
            # Include exception details if present
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)


class ColorFormatter(logging.Formatter):
    """Custom formatter to add color to log levels in console output."""
    COLOR_CODES = {
        "DEBUG": "\033[37m",  # White
        "INFO": "\033[32m",   # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[1;31m",  # Bold Red
    }
    RESET_CODE = "\033[0m"

    def format(self, record):
        # Apply color to the log level
        color = self.COLOR_CODES.get(record.levelname, self.RESET_CODE)
        record.levelname = f"{color}{record.levelname}{self.RESET_CODE}"
        return super().format(record)


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
DEFAULT_LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'readable': {
            'format': '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] - %(message)s',
        },
        'json': {
            '()': JSONFormatter,  # Use the custom JSON formatter
            'session': 'default',
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
            'handlers': ['console', 'redis'],
        }
    }
}

PROD_LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'readable': {
            'format': '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] - %(message)s',
        },
        'json': {
            '()': JSONFormatter,  # Use the custom JSON formatter
            'session': 'default',
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
            'redis_host': 'redis',
            'redis_port': 6379,
            'channel': 'log_channel',
        },
    },
    'loggers': {
        '': {  # Root logger
            'level': 'INFO',
            'handlers': ['console', 'redis'],
        }
    }
}

def is_redis_connected(host: str, port: int) -> bool:
    from redis.exceptions import ConnectionError
    try:
        redis_client = redis.Redis(host=host, port=port)
        redis_client.ping()
        return True
    except ConnectionError:
        return False

def setup_logging(session: str = None):
    """Sets up logging based on the configuration."""
    if is_redis_connected(DEFAULT_LOGGING_CONFIG['handlers']['redis']['redis_host'], 
                          DEFAULT_LOGGING_CONFIG['handlers']['redis']['redis_port']):
        logging_config = DEFAULT_LOGGING_CONFIG
    elif is_redis_connected(PROD_LOGGING_CONFIG['handlers']['redis']['redis_host'], 
                            PROD_LOGGING_CONFIG['handlers']['redis']['redis_port']):
        logging_config = PROD_LOGGING_CONFIG
    else:
        raise ConnectionError("Failed to connect to Redis server")
    if session:
        logging_config['formatters']['json']['session'] = session
    logging.config.dictConfig(logging_config)
    

# Global exception hook
def log_uncaught_exceptions(exc_type, exc_value, exc_traceback):
    """Logs uncaught exceptions."""
    logger = logging.getLogger()
    if issubclass(exc_type, KeyboardInterrupt):
        # Ignore KeyboardInterrupt to allow graceful shutdown
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.error("Unhandled exception occurred",
                 exc_info=(exc_type, exc_value, exc_traceback))

# Set up the logging and global exception hook
setup_logging()
sys.excepthook = log_uncaught_exceptions

def getLogger(name=None):
    """
    Returns a logger instance with the specified name.
    """
    return logging.getLogger(name)

# Example to test unhandled exceptions
if __name__ == "__main__":
    logger = getLogger()
    try:
        raise ValueError("Test exception for demonstration")
    except Exception as e:
        logger.exception("Handled exception occurred")
    # Uncomment the following line to test unhandled exceptions
    # raise RuntimeError("Unhandled exception for demonstration")
