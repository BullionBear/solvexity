import os
from typing import Type
from solvexity.trader.core import Strategy, Signal, Policy, SignalType
from solvexity.trader.report import Report
import solvexity.helper.logging as logging

logger = logging.getLogger()

class Pythagoras(Strategy):
    REPORT_BUFFER_SIZE = 65535
    def __init__(self, signal: Type[Signal], policy: Type[Policy], symbol: str, granular: str, trade_id: str, verbose: bool = False):
        super().__init__(trade_id)
        self.signal = signal
        self.policy = policy
        self.symbol = symbol
        self.granular = granular
        self.verbose = verbose
        self.output_dir = os.path.join(os.getcwd(), "verbose", self.id)
        self.report = Report(self.signal.get_context(), self.symbol, self.granular, self.REPORT_BUFFER_SIZE)
        if self.verbose:
            logger.info(f"Verbose mode is enabled. Output directory: {self.output_dir}")
            os.makedirs(self.output_dir, exist_ok=True)
        self.policy.notify("OnTradingStart", f"**Trade ID**: {self.id}", 0x00FF00) # Green
        
    def invoke(self):
        self.report.invoke() # Invoke report before executing the strategy
        s = self.signal.solve()
        logger.info(f"Signal: {s}")
        if s == SignalType.BUY:
            self.policy.buy()
        elif s == SignalType.SELL:
            self.policy.sell()
        
        if self.verbose:
            self.signal.visualize(self.output_dir)
            self.signal.export(self.output_dir)
    
    def close(self):
        self.policy.notify("OnTradingFinish", f"**Trade ID**: {self.id}", 0x00FF00) # Green
        if self.verbose:
            self.report.export(self.output_dir)
            self.policy.export(self.output_dir)
            logger.info(f"Trading report is exported to {self.output_dir}")