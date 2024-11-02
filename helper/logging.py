import logging
import logging.config
import json
import os

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
