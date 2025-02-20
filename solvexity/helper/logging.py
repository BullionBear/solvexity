import logging
import logging.config
import json
import sys
import uuid
import grpc
from solvexity.generated import logger_pb2, logger_pb2_grpc

def setup_logging(config: dict):
    """Sets up logging based on the configuration."""
    logging.config.dictConfig(config)

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
    
class LoggerServiceHandler(logging.Handler):
    def __init__(self, host='localhost', port=50051):
        super().__init__()
        self.host = host
        self.port = port
        # Create a gRPC channel and stub
        self.channel = grpc.insecure_channel(f'{self.host}:{self.port}')
        self.stub = logger_pb2_grpc.LoggerStub(self.channel)

    def emit(self, record):
        """
        Send the log message to the gRPC logger service.
        """
        try:
            # Format the log message
            log_message = self.format(record)

            # Map Python logging levels to gRPC LogLevel enum
            level_mapping = {
                logging.DEBUG: logger_pb2.LogLevel.DEBUG,
                logging.INFO: logger_pb2.LogLevel.INFO,
                logging.WARNING: logger_pb2.LogLevel.WARNING,
                logging.ERROR: logger_pb2.LogLevel.ERROR,
                logging.CRITICAL: logger_pb2.LogLevel.ERROR,  # Map CRITICAL to ERROR
            }

            # Get the corresponding gRPC log level
            log_level = level_mapping.get(record.levelno, logger_pb2.LogLevel.INFO)

            # Create a LogRequest message
            log_request = logger_pb2.LogRequest(
                message=log_message,
                level=log_level
            )

            # Send the log message to the gRPC server
            self.stub.Log(iter([log_request]))

        except Exception as e:
            # Handle any errors that occur during logging
            print(f"Failed to send log message to gRPC server: {e}")

    def close(self):
        """
        Clean up the gRPC channel when the handler is closed.
        """
        self.channel.close()
        super().close()


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
        'grpc': {
            '()': LoggerServiceHandler,  # Use the custom Redis handler
            'level': 'INFO',
            'formatter': 'json',
            'host': 'localhost',
            'port': 3000
        },
    },
    'loggers': {
        '': {  # Root logger
            'level': 'INFO',
            'handlers': ['console', 'grpc'],
        }
    }
}


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
