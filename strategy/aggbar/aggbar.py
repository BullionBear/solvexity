from solvexity.model.trade import Trade
from solvexity.model.bar import Bar
from solvexity.model.shared import Side
from enum import Enum


import logging
logger = logging.getLogger(__name__)

class BarType(Enum):
    TIME_BAR = "TimeBar"
    TICK_BAR = "TickBar"
    BASE_VOLUME_BAR = "BaseVolumeBar"
    QUOTE_VOLUME_BAR = "QuoteVolumeBar"

    

class AggBar:
    def __init__(self, buf_size: int, reference_cutoff: int, bar_type: BarType):
        self.buf_size = buf_size
        self.bar_type = bar_type
        self.bar_ref_cutoff = reference_cutoff # Different type represents different reference cutoff
        self.method_dict = {
            BarType.TIME_BAR: self.on_time_bar,
            BarType.TICK_BAR: self.on_tick_bar,
            BarType.BASE_VOLUME_BAR: self.on_base_volume_bar,
            BarType.QUOTE_VOLUME_BAR: self.on_quote_volume_bar,
        }
        self.on_trade_aggregation = self.method_dict[bar_type]

        self._accumulator = 0
        self._reference_index = 0
        self._finished_bars = 0
        self.bars: list[Bar|None] = [None for _ in range(buf_size)]

    async def on_trade(self, trade: Trade):
        # logger.info(f"On trade: {trade}")
        try:
            self.on_trade_aggregation(trade)
        except AttributeError as e:
            logger.error(f"AttributeError on trade: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Exception on trade: {e}", exc_info=True)
            raise


    def on_time_bar(self, trade: Trade):
        self._accumulator = trade.timestamp
        next_reference_index = int(self._accumulator // self.bar_ref_cutoff)
        if next_reference_index == self._reference_index:
            self.bars[self._reference_index % self.buf_size] += trade
        elif next_reference_index > self._reference_index:
            self.bars[next_reference_index % self.buf_size] = Bar(trade)
            if self.bars[self._reference_index % self.buf_size] is not None:
                self.bars[self._reference_index % self.buf_size].enclose(trade.timestamp)
                logger.info(f"Finished time bar: {self.bars[self._reference_index % self.buf_size]}")
            self._reference_index = next_reference_index
            self._finished_bars += 1            
        else:
            logger.warning(f"Invalid reference index: {self._reference_index} and next reference index: {next_reference_index}")

    def on_tick_bar(self, trade: Trade):
        self._accumulator += 1
        next_reference_index = int(self._accumulator // self.bar_ref_cutoff)
        if next_reference_index == self._reference_index:
            self.bars[self._reference_index % self.buf_size] += trade
        elif next_reference_index > self._reference_index:
            self.bars[next_reference_index % self.buf_size] = Bar(trade)
            self.bars[self._reference_index % self.buf_size].enclose(trade.timestamp)
            logger.info(f"Finished tick bar: {self.bars[self._reference_index % self.buf_size]}")
            self._reference_index = next_reference_index
            self._finished_bars += 1
        else:
            logger.warning(f"Invalid reference index: {self._reference_index} and next reference index: {next_reference_index}")

    def on_base_volume_bar(self, trade: Trade):
        self._accumulator += trade.quantity
        next_reference_index = int(self._accumulator // self.bar_ref_cutoff)
        if next_reference_index == self._reference_index:
            self.bars[self._reference_index % self.buf_size] += trade
        elif next_reference_index > self._reference_index:
            remainder = self._accumulator % self.bar_ref_cutoff
            trade_left = trade.model_copy(deep=False)
            trade_right = trade.model_copy(deep=False)

            trade_left.quantity = remainder
            trade_right.quantity = trade.quantity - remainder
            self.bars[self._reference_index % self.buf_size] += trade_left
            self.bars[self._reference_index % self.buf_size].next_id = trade_right.id
            self.bars[self._reference_index % self.buf_size].enclose(trade.timestamp)
            logger.info(f"Finished base volume bar: {self.bars[self._reference_index % self.buf_size]}")
            self._finished_bars += 1
            self.bars[next_reference_index % self.buf_size] = Bar(trade_right)
            self._reference_index = next_reference_index
            self._finished_bars += 1
        else:
            logger.warning(f"Invalid reference index: {self._reference_index} and next reference index: {next_reference_index}")

    def on_quote_volume_bar(self, trade: Trade):
        self._accumulator += trade.price * trade.quantity
        next_reference_index = int(self._accumulator // self.bar_ref_cutoff)
        if next_reference_index == self._reference_index:
            self.bars[self._reference_index % self.buf_size] += trade
        elif next_reference_index > self._reference_index:
            remainder = self._accumulator % self.bar_ref_cutoff
            trade_left = trade.model_copy(deep=False)
            trade_right = trade.model_copy(deep=False)
            trade_left.quantity = remainder / trade.price
            trade_right.quantity = trade.quantity - trade_left.quantity
            self.bars[self._reference_index % self.buf_size] += trade_left
            self.bars[self._reference_index % self.buf_size].next_id = trade_right.id
            self.bars[self._reference_index % self.buf_size].enclose(trade.timestamp)
            logger.info(f"Finished quote volume bar: {self.bars[self._reference_index % self.buf_size]}")
            self._finished_bars += 1
            self.bars[next_reference_index % self.buf_size] = Bar(trade_right)
            self._reference_index = next_reference_index
        else:
            logger.warning(f"Invalid reference index: {self._reference_index} and next reference index: {next_reference_index}")