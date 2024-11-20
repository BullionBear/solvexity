from typing import Type
from trader.core import Strategy, TradeContext, Policy, Signal, SignalType
from service.socket_argparser import SocketArgparser

class Archimedes(Strategy):
    def __init__(self, trade_context: Type[TradeContext], signal: Type[Signal], policy: Type[Policy], tcp_server: SocketArgparser, trade_id = None):
        super().__init__(trade_context, trade_id)
        self.signal = signal
        self.policy = policy
        self.tcp_server = tcp_server

    def invoke(self):
        if self.signal.solve() == SignalType.BUY:
            self.policy.buy()
        elif self.signal.solve() == SignalType.SELL:
            self.policy.sell()
        else:
            pass