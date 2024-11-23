from typing import Type
from trader.core import Signal, Policy, SignalType
from trader.core import Strategy, Signal, Policy
import helper.logging as logging

logger = logging.getLogger("trading")

class Pythagoras(Strategy):
    def __init__(self, signal: Type[Signal], policy: Type[Policy], trade_id: str):
        super().__init__(trade_id)
        self.signal = signal
        self.policy = policy
    
        
    def invoke(self):
        s = self.signal.solve()
        if s == SignalType.BUY:
            self.policy.buy()
        elif s == SignalType.SELL:
            self.policy.sell()
        else:
            pass
