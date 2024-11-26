import logging
import logging.config
import json

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

# Define a centralized logging configuration with JSON and colorful readable formatters
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'readable': {
            '()': ColorFormatter,  # Use the custom color formatter for console
            'format': '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] - %(message)s',
        },
        'json': {
            '()': JSONFormatter,  # Use the custom JSON formatter for file logs
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'readable',  # Colorful human-readable format for console
            'stream': 'ext://sys.stdout',
        },
        'file': {
            'class': 'logging.FileHandler',
            'level': 'INFO',
            'formatter': 'json',  # JSON format for file output
            'filename': './log/process.log',
            'mode': 'a',
        },
    },
    'loggers': {
        '': {  # Root logger
            'level': 'INFO',
            'handlers': ['console', 'file'],
        },
        'trading': {
            'level': 'INFO',
            'handlers': ['console', 'file'],
            'propagate': False
        },
        'data': {
            'level': 'INFO',
            'handlers': ['console', 'file'],
            'propagate': False
        },
        'server': {
            'level': 'INFO',
            'handlers': ['console', 'file'],
            'propagate': False
        }
    }
}

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

# Example usage of the centralized logger
if __name__ == "__main__":
    # Initialize logging
    setup_logging()

    # Get a logger instance
    logger = logging.getLogger("my_module")

    # Log messages with different severity levels
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
