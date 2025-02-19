import logging
import grpc
import argparse
from concurrent import futures
from solvexity.generated import logger_pb2, logger_pb2_grpc
from solvexity.helper.utils import load_config

class LoggerServicer(logger_pb2_grpc.LoggerServicer):
    def Log(self, request_iterator, context):
        total_logs_received = 0

        # Process each log message in the stream
        for log_request in request_iterator:
            level = log_request.level
            message = log_request.message

            # Log the message with the appropriate level
            if level == logger_pb2.LogLevel.DEBUG:
                logging.debug(message)
            elif level == logger_pb2.LogLevel.INFO:
                logging.info(message)
            elif level == logger_pb2.LogLevel.WARNING:
                logging.warning(message)
            elif level == logger_pb2.LogLevel.ERROR:
                logging.error(message)
            else:
                logging.info(f"Unknown log level: {level}. Message: {message}")

            total_logs_received += 1

        # Return a summary response
        return logger_pb2.LogResponse(
            total_logs_received=total_logs_received,
            success=True
        )

def serve(config_path: str):
    # Load the configuration
    config = load_config(config_path)
    # Configure logging
    logging.basicConfig(level=logging.DEBUG)  # Set to DEBUG to see all log levels

    # Create a gRPC server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # Add the Logger service to the server
    logger_pb2_grpc.add_LoggerServicer_to_server(LoggerServicer(), server)

    # Listen on port 50051
    port = config.get('port', 50051)
    server.add_insecure_port(f'[::]:{port}')
    print(f"Logger server running on port {port}...")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Run the gRPC server.")
    parser.add_argument(
        "-c", "--config",
        required=True,
        help="Path to the configuration file (JSON format)"
    )
    args = parser.parse_args()
    serve(args.config)