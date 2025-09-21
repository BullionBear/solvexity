from solvexity.model.trade import Trade
from solvexity.model.bar import Bar

import logging
logger = logging.getLogger(__name__)


class AggBar:
    def __init__(self, symbol: str, interval: str):
        self.symbol = symbol
        self.interval = interval
        self.bars: list[Bar] = []

    def on_trade(self, trade: Trade):
        logger.info(f"On trade: {trade}")
        pass