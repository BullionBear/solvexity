from solvexity.model.trade import Trade
from solvexity.model.bar import Bar
from enum import Enum


import logging
logger = logging.getLogger(__name__)

class BarType(Enum):
    TIME_BAR = "TimeBar"
    TICK_BAR = "TickBar"
    BASE_VOLUME_BAR = "BaseVolumeBar"
    QUOTE_VOLUME_BAR = "QuoteVolumeBar"

class AggBar:
    def __init__(self, buf_size: int, bar_type: BarType):
        self.buf_size = buf_size
        self.bar_type = bar_type
        self.bars: list[Bar] = []

    async def on_trade(self, trade: Trade):
        logger.info(f"On trade: {trade}")
        pass