import os
from typing import Type
from trader.core import StrategyV2, Policy, Signal, SignalType
from service.socket_argparser import SocketArgparser
import helper.logging as logging
from .notification import (
    on_trading_start, on_trading_finish, on_order_sent, on_error
)

logger = logging.getLogger("trading")


class Archimedes(StrategyV2):
    FAMILY = "Archimedes"
    def __init__(self, signal: Type[Signal], policy: Type[Policy], tcp_server: SocketArgparser, symbol: str, verbose:bool=False, output_dir: str = "./verbose", trade_id = None):
        super().__init__(signal, policy, trade_id)
        self.tcp_server = tcp_server
        self.symbol = symbol
        self.verbose = verbose
        self.output_dir = output_dir

    def __enter__(self):
        self.trade_context.notify(**on_trading_start(self.FAMILY, id=self.id, symbol=self.symbol))
        self.tcp_server.start_socket_server()
        os.makedirs(self.output_dir, exist_ok=True)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
    # Check if an exception occurred
        if exc_type is not None:
        # Log or display the error details
            error_message = f"Error in {self.FAMILY} strategy: {exc_type.__name__} - {exc_val}"
            self.trade_context.notify(error=error_message, id=self.id, symbol=self.symbol)

            # Optionally, handle the traceback or print it
            import traceback
            traceback_str = ''.join(traceback.format_exception(exc_type, exc_val, exc_tb))
            logger.error(traceback_str)  # Or use logging instead of print

        # Notify the trading finish regardless of error
        self.context().notify(**on_trading_finish(self.family, id=self.id, symbol=self.symbol))
        self.tcp_server.close()
        return False  # Propagate the exception if needed
    
    def context(self):
        return super().signal.trade_context
    
    @property
    def id(self):
        return super().id

    def invoke(self):
        if self.signal.solve() == SignalType.BUY:
            self.policy.buy()
        elif self.signal.solve() == SignalType.SELL:
            self.policy.sell()
        else:
            pass

        if self.verbose:
            self.signal.export(self.output_dir)
            self.signal.visualize(self.output_dir)