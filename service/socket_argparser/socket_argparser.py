import socketserver
import threading
import json
from typing import Callable, Dict, Optional
import helper.logging as logging

logger = logging.getLogger("tcp")


class SocketArgparser:
    def __init__(self, host: str, port: int):
        self.host: str = host
        self.port: int = port
        self.commands: Dict[str, Callable[[list], str]] = {}
        self.server: Optional[socketserver.ThreadingTCPServer] = None
        self.server_thread: Optional[threading.Thread] = None
        self.register_command("ping", self.ping_handler)

    def register_command(self, command: str, handler: Callable[[list], str]) -> None:
        """
        Register a command with a handler function.
        :param command: Command name
        :param handler: Handler function for the command
        """
        self.commands[command] = handler
        logger.info(f"Registered command: {command}")

    def start_socket_server(self) -> None:
        """
        Start a socket server using socketserver.
        """
        class CommandHandler(socketserver.BaseRequestHandler):
            """
            Request handler for processing commands.
            """
            def handle(self) -> None:
                # Receive the command data
                data = self.request.recv(1024).decode().strip()
                if data:
                    logger.info(f"Received command: {data}")
                    response = self.server.strategy._process_command(data)
                    self.request.sendall(response.encode())

        class StrategyServer(socketserver.ThreadingTCPServer):
            """
            Custom TCP server to attach strategy.
            """
            allow_reuse_address = True

            def __init__(self, server_address: tuple, handler_class: Callable[..., socketserver.BaseRequestHandler], strategy: 'SocketArgparser'):
                super().__init__(server_address, handler_class)
                self.strategy: 'SocketArgparser' = strategy

        # Create the server and start it in a thread
        self.server = StrategyServer((self.host, self.port), CommandHandler, self)
        self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.server_thread.start()
        logger.info(f"Socket server running on {self.host}:{self.port}")

    def _process_command(self, command_line: str) -> str:
        """
        Parse and process an incoming command.
        :param command_line: Raw command string
        :return: Response string
        """
        parts = command_line.split()
        if not parts:
            return json.dumps({"error": "Empty command"})

        command = parts[0]
        args = parts[1:]

        if command in self.commands:
            return self.commands[command](args)
        else:
            return json.dumps({"error": "Unknown command"})

    def close(self) -> None:
        """
        Gracefully shutdown the server.
        """
        if self.server:
            logger.info("Shutting down the server...")
            self.server.shutdown()  # Stop the serve_forever loop
            self.server.server_close()  # Close the server socket
            self.server = None

        if self.server_thread:
            self.server_thread.join()  # Wait for the thread to finish
            self.server_thread = None
        logger.info("Server has been shut down.")

    def ping_handler(self, args: list) -> str:
        """
        Handler function for the 'ping' command.
        :param args: List of arguments for the command
        :return: Response as a JSON string
        """
        return json.dumps({"response": "pong"})