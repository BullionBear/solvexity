import socketserver
import argparse
import threading
from typing import Type
from abc import ABC, abstractmethod
from trader.data import KLine
from .trade_context import TradeContext
from decimal import Decimal
import helper

class Strategy(ABC):
    def __init__(self, trade_context: Type[TradeContext], trade_id: str = None):
        self.trade_context = trade_context
        self.commands = {}
        if trade_id:
            self._id = trade_id
        else:
            self._id = helper.generate_random_id()


    @abstractmethod
    def invoke(self, klines: list[KLine]):
        pass

    def market_buy(self, symbol: str, size: Decimal):
        self.trade_context.market_buy(symbol, size)

    def market_sell(self, symbol: str, size: Decimal):
        self.trade_context.market_sell(symbol, size)

    def get_balance(self, token: str) -> Decimal:
        return self.trade_context.get_balance(token)
    
    def get_klines(self, symbol: str, limit: int) -> list[KLine]:
        return self.trade_context.get_klines(symbol, limit)
    
    def notify(self, **kwargs):
        self.trade_context.notify(**kwargs)
    
    def register_command(self, command: str, handler):
        """
        Register a command with a handler function.
        :param command: Command name (string)
        :param handler: Handler function for the command
        """
        self.commands[command] = handler
        print(f"{self.commands}")

    def start_socket_server(self, host: str, port: int):
        """
        Start a socket server using socketserver.
        :param host: Host address to bind
        :param port: Port to bind
        """
        class CommandHandler(socketserver.BaseRequestHandler):
            """
            Request handler for processing commands.
            """
            def handle(self):
                # Receive the command data
                data = self.request.recv(1024).decode().strip()
                if data:
                    print(f"Received command: {data}")
                    response = self.server.strategy._process_command(data)
                    self.request.sendall(response.encode())

        class StrategyServer(socketserver.ThreadingTCPServer):
            """
            Custom TCP server to attach strategy.
            """
            allow_reuse_address = True

            def __init__(self, server_address, handler_class, strategy):
                super().__init__(server_address, handler_class)
                self.strategy = strategy

        # Create the server and start it in a thread
        server = StrategyServer((host, port), CommandHandler, self)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        print(f"Socket server running on {host}:{port}")

    def _process_command(self, command_line: str) -> str:
        """
        Parse and process an incoming command.
        :param command_line: Raw command string
        :return: Response string
        """
        parser = argparse.ArgumentParser(prog="command")
        subparsers = parser.add_subparsers(dest="command")

        # Dynamically add registered commands to the parser
        for command, handler in self.commands.items():
            subparser = subparsers.add_parser(command)
            handler(subparser)

        try:
            args = parser.parse_args(command_line.split())
            if args.command in self.commands:
                return self.commands[args.command](args)
            else:
                return "Unknown command"
        except SystemExit:
            return "Error in command parsing"