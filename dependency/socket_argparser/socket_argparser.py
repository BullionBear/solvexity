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
        self.commands: Dict[str, Callable[[argparse.ArgumentParser], Callable[[argparse.Namespace], str]]] = {}
        self.server: Optional[socketserver.ThreadingTCPServer] = None
        self.server_thread: Optional[threading.Thread] = None
        self.register_command("ping", self.ping_command)
        self.register_command("help", self.help_command)
        self.register_command("bye", self.bye_command)

        # self.register_command("echo", self.echo_command)

    def register_command(self, command: str, command_func: Callable[[argparse.ArgumentParser], Callable[[argparse.Namespace], str]]) -> None:
        """
        Register a command with a combined parser and handler function.
        :param command: Command name
        :param command_func: Function that sets up the parser and returns a handler
        """
        self.commands[command] = command_func
        logger.info(f"Registered command: {command}")

    def start_socket_server(self) -> None:
        """
        Start a socket server using socketserver.
        """
        class CommandHandler(socketserver.BaseRequestHandler):
            def handle(self) -> None:
                self.request.sendall("Welcome to the server! Type 'help' for available commands.\n".encode())
                while True:
                    self.request.sendall("> ".encode())
                    data = self.request.recv(1024).decode().strip()
                    if not data:
                        logger.info("No data found.")
                        continue

                    logger.info(f"Received command: {data}")
                    response = self.server.strategy._process_command(data)

                    if response:
                        self.request.sendall(f"{response}\n".encode())

                    if data.split()[0].lower() == "bye":
                        logger.info("Client requested to disconnect.")
                        self.request.sendall("Goodbye!\n".encode())
                        break

        class StrategyServer(socketserver.ThreadingTCPServer):
            allow_reuse_address = True

            def __init__(self, server_address: tuple, handler_class: Callable[..., socketserver.BaseRequestHandler], strategy: 'SocketArgparser'):
                super().__init__(server_address, handler_class)
                self.strategy: 'SocketArgparser' = strategy

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
                return self.commands["help"](argparse.ArgumentParser())([])

            parser = argparse.ArgumentParser(prog=command)
            handler = self.commands[command](parser)

            args = parser.parse_args(command_parts[1:])
            return handler(args)

        except SystemExit:
            return "Invalid arguments. Use 'help' for more information."
        except Exception as e:
            logger.error(f"Error processing command: {e}")
            return "An error occurred while processing your command."

    def close(self) -> None:
        if self.server:
            logger.info("Shutting down the server...")
            self.server.shutdown()
            self.server.server_close()
            self.server = None

        if self.server_thread:
            self.server_thread.join()
            self.server_thread = None
        logger.info("Server has been shut down.")

    # Example Combined Command Definitions
    def ping_command(self, parser: argparse.ArgumentParser) -> Callable[[argparse.Namespace], str]:
        """
        Defines the 'ping' command parser and handler.
        """
        def handler(args: argparse.Namespace) -> str:
            return "pong!"
        return handler

    def help_command(self, parser: argparse.ArgumentParser) -> Callable[[argparse.Namespace], str]:
        """
        Defines the 'help' command parser and handler.
        """
        def handler(args: argparse.Namespace) -> str:
            return f"Available commands: {', '.join(self.commands.keys())}"
        return handler

    def bye_command(self, parser: argparse.ArgumentParser) -> Callable[[argparse.Namespace], str]:
        """
        Defines the 'bye' command parser and handler.
        """
        def handler(args: argparse.Namespace) -> str:
            return ''
        return handler
    """
    def echo_command(self, parser: argparse.ArgumentParser) -> Callable[[argparse.Namespace], str]:
        /*
        Defines the 'echo' command parser and handler.
        */
        parser.add_argument("message", type=str, help="Message to echo")

        def handler(args: argparse.Namespace) -> str:
            return f"Echo: {args.message}"
        return handler
    """