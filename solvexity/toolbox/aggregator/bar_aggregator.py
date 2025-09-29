from collections import deque
from solvexity.model.trade import Trade
from solvexity.model.bar import Bar
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class BarType(Enum):
    TIME = "time"
    TICK = "tick"
    BASE_VOLUME = "base_volume"
    QUOTE_VOLUME = "quote_volume"

class TimeBarAggregator:
    def __init__(self, buf_size: int, reference_cutoff: int):
        self.buf_size = buf_size
        self.reference_cutoff = reference_cutoff

        self.bars: deque[Bar] = deque(maxlen=buf_size)
        self.accumulator = 0

    def reset(self):
        self.bars.clear()
        self.accumulator = 0

    def on_trade(self, trade: Trade):
        self.accumulator = trade.timestamp
        if len(self.bars) == 0:
            self.bars.append(Bar.from_trade(trade))
            self.bars[-1].open_time = self.accumulator // self.reference_cutoff * self.reference_cutoff
            return
        prev_reference_index = self.bars[-1].close_time // self.reference_cutoff
        next_reference_index = int(self.accumulator // self.reference_cutoff)
        if prev_reference_index == next_reference_index:
            self.bars[-1] += trade
        elif next_reference_index > prev_reference_index:
            self.bars[-1].enclose(next_reference_index * self.reference_cutoff - 1)
            logger.info(f"Enclose time bar: {self.bars[-1]}")
            self.bars.append(Bar.from_trade(trade))
            self.bars[-1].open_time = next_reference_index * self.reference_cutoff
        else:
            self.reset()
            logger.error(f"Invalid reference index: {prev_reference_index} and next reference index: {next_reference_index}")

class TickBarAggregator:
    def __init__(self, buf_size: int, reference_cutoff: int):
        self.buf_size = buf_size
        self.reference_cutoff = reference_cutoff
        
        self.bars: deque[Bar] = deque(maxlen=buf_size)
        self.accumulator = 0

    def reset(self):
        self.bars.clear()
        self.accumulator = 0

    def on_trade(self, trade: Trade):
        self.accumulator = trade.id
        if len(self.bars) == 0:
            self.bars.append(Bar.from_trade(trade))
            return
        prev_reference_index = self.bars[-1].current_id // self.reference_cutoff
        next_reference_index = int(self.accumulator // self.reference_cutoff)
        if prev_reference_index == next_reference_index:
            self.bars[-1] += trade
        elif next_reference_index > prev_reference_index:
            self.bars[-1].enclose(trade.timestamp - 1)
            logger.info(f"Enclose tick bar: {self.bars[-1]}")
            self.bars.append(Bar.from_trade(trade))
        else:
            self.reset()
            logger.error(f"Invalid reference index: {prev_reference_index} and next reference index: {next_reference_index}")


class BaseVolumeBarAggregator:
    def __init__(self, buf_size: int, reference_cutoff: float):
        self.buf_size = buf_size
        self.reference_cutoff = reference_cutoff
        self.bars: deque[Bar] = deque(maxlen=buf_size)
        self.accumulator = 0

    def reset(self):
        self.bars.clear()
        self.accumulator = 0

    def on_trade(self, trade: Trade):
        while abs(trade.quantity) > 2 * 1e-13: # python's float precision is estimated to 15-17 digits
            if len(self.bars) == 0 or self.bars[-1].is_closed:
                empty_trade = trade.model_copy(deep=False)
                empty_trade.quantity = 0
                self.bars.append(Bar.from_trade(empty_trade))

            need = self.reference_cutoff - self.accumulator % self.reference_cutoff
            if abs(trade.quantity - need) < 2 * 1e-13: # trade.quantity = need                
                self.bars[-1] += trade
                self.bars[-1].enclose(trade.timestamp)
                logger.info(f"Enclose base volume bar: {self.bars[-1]} with {trade.quantity=} ~ {need=}")
                self.accumulator += need + 1e-13
                trade.quantity = 0
            elif trade.quantity < need:
                self.bars[-1] += trade
                self.accumulator += trade.quantity
                trade.quantity = 0
                
            elif trade.quantity > need:
                trade_fraction = trade.model_copy(deep=False)
                trade_fraction.quantity = need
                self.bars[-1] += trade_fraction
                self.bars[-1].enclose(trade.timestamp)
                self.bars[-1].next_id = trade.id
                logger.info(f"Enclose base volume bar: {self.bars[-1]} with {trade.quantity=} > {need=}")
                trade.quantity -= need
                self.accumulator += need + 1e-13
            else:
                self.reset()
                logger.error(f"Undefined behavior: {self.accumulator=} and {trade.quantity=} and {need=}")
                break


class QuoteVolumeBarAggregator:
    def __init__(self, buf_size: int, reference_cutoff: float):
        self.buf_size = buf_size
        self.reference_cutoff = reference_cutoff
        self.bars: deque[Bar] = deque(maxlen=buf_size)
        self.accumulator = 0

    def reset(self):
        self.bars.clear()
        self.accumulator = 0

    def on_trade(self, trade: Trade):
        while abs(trade.quantity) > 2 * 1e-13: # python's float precision is estimated to 15-17 digits
            if len(self.bars) == 0 or self.bars[-1].is_closed:
                empty_trade = trade.model_copy(deep=False)
                empty_trade.quantity = 0
                self.bars.append(Bar.from_trade(empty_trade))

            need_quote = self.reference_cutoff - self.accumulator % self.reference_cutoff
            need = need_quote / trade.price
            if abs(trade.quantity - need) < 2 * 1e-13: # trade.quantity = need                
                self.bars[-1] += trade
                self.bars[-1].enclose(trade.timestamp)
                logger.info(f"Enclose quote volume bar: {self.bars[-1]} with {trade.quantity=} ~ {need=}")
                self.accumulator += need_quote + 1e-13
                trade.quantity = 0
            elif trade.quantity < need:
                self.bars[-1] += trade
                self.accumulator += need_quote
                trade.quantity = 0
            elif trade.quantity > need:
                self.bars[-1] += trade
                self.bars[-1].enclose(trade.timestamp)
                self.bars[-1].next_id = trade.id
                logger.info(f"Enclose quote volume bar: {self.bars[-1]} with {trade.quantity=} > {need=}")
                self.accumulator += need_quote + 1e-13
                trade.quantity -= need
            else:
                self.reset()
                logger.error(f"Undefined behavior: {self.accumulator=} and {trade.quantity=} and {need_quote=}, {need=}")
                break