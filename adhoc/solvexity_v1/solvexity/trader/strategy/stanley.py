import os
import time
from typing import Type
from solvexity.trader.core import Strategy
from solvexity.trader.core import Strategy, Signal, Policy, SignalType
from solvexity.trader.report import Report
import solvexity.helper as helper
import solvexity.helper.logging as logging

logger = logging.getLogger()

class Stanley(Strategy):
    """
    Stanley is a strategy only runs with a finite time, the finite time can be 1 day, 1 week, or 1 month.  Any multiplier base on your granular the live_time
    """
    def __init__(self, signal: Type[Signal], policy: Type[Policy], symbol: str, granular: str, live_time: int, trade_id: str, verbose: bool = False):
        super().__init__(trade_id)
        self.signal = signal
        self.policy = policy
        self.symbol = symbol
        self.granular = granular
        self.live_time = live_time
        self.verbose = verbose

        self._start_time = int(time.time() * 1000)
        self._end_time = self._start_time + helper.to_unixtime_interval(self.granular) * self.live_time
        logger.info(f"Start time: {helper.to_isoformat(self._start_time)}, Target end time: {helper.to_isoformat(self._end_time)}")
    
    def invoke(self):
        # Run the strategy
        if int(time.time() * 1000) > self._end_time:
            return
        s = self.signal.solve()
        logger.info(f"Signal: {s}")
        if s == SignalType.BUY:
            self.policy.buy()
        elif s == SignalType.SELL:
            self.policy.sell()
        else:
            pass



    

        