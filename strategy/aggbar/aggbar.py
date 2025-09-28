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
        self._reference_index = -1
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
            self.bars[next_reference_index % self.buf_size] = Bar.from_trade(trade)
            self.bars[next_reference_index % self.buf_size].open_time = next_reference_index * self.bar_ref_cutoff
            if bar := self.bars[self._reference_index % self.buf_size]:
                bar.enclose(next_reference_index * self.bar_ref_cutoff - 1)
                logger.info(f"Finished {self._finished_bars}'th time bar: {bar}")
                self._finished_bars += 1
            self._reference_index = next_reference_index
        else:
            logger.warning(f"Invalid reference index: {self._reference_index} and next reference index: {next_reference_index}")

    def on_tick_bar(self, trade: Trade):
        self._accumulator = trade.id
        next_reference_index = int(self._accumulator // self.bar_ref_cutoff)
        if next_reference_index == self._reference_index:
            self.bars[self._reference_index % self.buf_size] += trade
        elif next_reference_index > self._reference_index:
            self.bars[next_reference_index % self.buf_size] = Bar.from_trade(trade)
            if bar := self.bars[self._reference_index % self.buf_size]:
                bar.enclose(trade.timestamp)
                logger.info(f"Finished {self._finished_bars}'th tick bar: {bar}")
                self._finished_bars += 1
            self._reference_index = next_reference_index
        else:
            logger.warning(f"Invalid reference index: {self._reference_index} and next reference index: {next_reference_index}")

    def on_base_volume_bar(self, trade: Trade):
        if self._reference_index == -1:
            self._reference_index = 0

        while abs(trade.quantity) > 2 * 1e-13: # python's float precision is estimated to 15-17 digits
            need = self.bar_ref_cutoff - self._accumulator % self.bar_ref_cutoff
            next_reference_index = int(self._accumulator // self.bar_ref_cutoff)
            empty_trade = trade.model_copy(deep=False)
            empty_trade.quantity = 0
            if next_reference_index > self._reference_index:
                self.bars[next_reference_index % self.buf_size] = Bar.from_trade(empty_trade)
                self._reference_index = next_reference_index
            if abs(trade.quantity - need) < 2 * 1e-13: # trade.quantity = need                
                if bar := self.bars[self._reference_index % self.buf_size]:
                    bar += trade
                else:
                    bar = Bar.from_trade(trade)
                    self.bars[self._reference_index % self.buf_size] = bar
                bar.enclose(trade.timestamp)
                self._finished_bars += 1
                logger.info(f"Finished {self._finished_bars}'th base volume bar: {bar}")
                self._accumulator += need + 1e-13
                self._reference_index += 1
                trade.quantity = 0
            elif trade.quantity < need:
                if bar := self.bars[self._reference_index % self.buf_size]:
                    bar += trade
                else:
                    bar = Bar.from_trade(trade)
                    self.bars[self._reference_index % self.buf_size] = bar
                self._accumulator += trade.quantity
                trade.quantity = 0
                
            elif trade.quantity > need:
                trade_fraction = trade.model_copy(deep=False)
                trade_fraction.quantity = need
                if bar := self.bars[self._reference_index % self.buf_size]:
                    bar += trade_fraction
                else:
                    bar = Bar.from_trade(trade_fraction)
                    self.bars[self._reference_index % self.buf_size] = bar
                bar.enclose(trade.timestamp)
                bar.next_id = trade.id
                self._finished_bars += 1
                logger.info(f"Finished {self._finished_bars}'th base volume bar: {bar}")
                trade.quantity -= need
                self._accumulator += need - 1e-13
            else:
                logger.error(f"Undefined behavior: {self._accumulator=} and {trade.quantity=} and {need=}")
            

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
            if bar := self.bars[self._reference_index % self.buf_size]:
                bar += trade_left
                bar.next_id = trade_right.id
                bar.enclose(trade.timestamp)
                logger.info(f"Finished {self._finished_bars}'th quote volume bar: {bar}")
                self._finished_bars += 1
            self.bars[next_reference_index % self.buf_size] = Bar.from_trade(trade_right)
            self._reference_index = next_reference_index
        else:
            logger.warning(f"Invalid reference index: {self._reference_index} and next reference index: {next_reference_index}")