import socketserver
import argparse
import threading
import json
from typing import Callable, Dict, Optional, Any
import helper.logging as logging

logger = logging.getLogger("tcp")

class SocketArgparser:
    def __init__(self, host: str, port: int):
        self.host: str = host
        self.port: int = port
        self.commands: Dict[str, Callable[[argparse.Namespace], str]] = {}
        self.server: Optional[socketserver.ThreadingTCPServer] = None
        self.server_thread: Optional[threading.Thread] = None
        self.register_command("ping", self.ping_handler)
        self.register_command("help", self.help_handler)
        self.register_command("bye", self.bye_handler)

    def register_command(self, command: str, handler: Callable[[argparse.Namespace], str]) -> None:
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
                # Send a welcome message
                self.request.sendall("Welcome to the server! Type 'help' for available commands.\n".encode())
                
                while True:
                    # Prompt the client
                    self.request.sendall("> ".encode())
                    
                    # Receive the command data
                    data = self.request.recv(1024).decode().strip()
                    if not data:  # Handle client disconnect
                        logger.info("No data found.")
                        continue

                    logger.info(f"Received command: {data}")
                    response = self.server.strategy._process_command(data)

                    if response:
                        self.request.sendall(f"{response}\n".encode())

                    # If the command is 'bye', break the loop and close the connection
                    if data.split()[0].lower() == "bye":
                        logger.info("Client requested to disconnect.")
                        self.request.sendall("Goodbye!\n".encode())
                        break

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
        try:
            command_parts = command_line.split()
            command = command_parts[0]
            if command not in self.commands:
                return self.commands["help"](argparse.Namespace())

            # Execute the command handler
            handler = self.commands[command]
            return handler(argparse.Namespace(args=command_parts[1:]))

        except Exception as e:
            logger.error(f"Error processing command: {e}")
            return "An error occurred while processing your command."

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

    def ping_handler(self, args: argparse.Namespace) -> str:
        """
        Handler function for the 'ping' command.
        :param args: Parsed arguments
        :return: Response as a JSON string
        """
        return "pong!"

    def help_handler(self, args: argparse.Namespace) -> str:
        """
        Handler function for the 'help' command.
        :param args: Parsed arguments
        :return: A list of available commands as a JSON string
        """
        return f"""Available commands: {', '.join(self.commands.keys())}"""

    def bye_handler(self, args: argparse.Namespace) -> str:
        """
        Handler function for the 'bye' command.
        :param args: Parsed arguments
        :return: A message indicating the client should disconnect
        """
        return ''