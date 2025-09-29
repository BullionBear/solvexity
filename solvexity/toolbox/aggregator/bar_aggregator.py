from solvexity.model.trade import Trade, Side
from solvexity.model.bar import Bar

import logging
logger = logging.getLogger(__name__)

class TimeBarAggregator:
    def __init__(self, buf_size: int, reference_cutoff: int):
        self.buf_size = buf_size
        self.reference_cutoff = reference_cutoff
        self.bars = [None] * buf_size
        self.reference_index = -1
        self.finished_bars = 0

    def reset(self):
        self.reference_index = -1
        self.finished_bars = 0
        self.bars = [None] * self.buf_size

    def on_trade(self, trade: Trade):
        self._accumulator = trade.timestamp
        next_reference_index = int(self._accumulator // self.reference_cutoff)
        if next_reference_index == self._reference_index:
            self.bars[self._reference_index % self.buf_size] += trade
        elif next_reference_index > self._reference_index:
            self.bars[next_reference_index % self.buf_size] = Bar.from_trade(trade)
            self.bars[next_reference_index % self.buf_size].open_time = next_reference_index * self.reference_cutoff
            if bar := self.bars[self._reference_index % self.buf_size]:
                bar.enclose(next_reference_index * self.reference_cutoff - 1)
                logger.info(f"Finished {self._finished_bars}'th time bar: {bar}")
                self._finished_bars += 1
            self._reference_index = next_reference_index
        else:
            logger.warning(f"Invalid reference index: {self._reference_index} and next reference index: {next_reference_index}")

class TickBarAggregator:
    def __init__(self, buf_size: int, reference_cutoff: int):
        self.buf_size = buf_size
        self.reference_cutoff = reference_cutoff
        self.bars = [None] * buf_size
        self.reference_index = -1
        self.finished_bars = 0

    def reset(self):
        self.reference_index = -1
        self.finished_bars = 0
        self.bars = [None] * self.buf_size

    def on_trade(self, trade: Trade):
        self._accumulator = trade.id
        next_reference_index = int(self._accumulator // self.reference_cutoff)
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


class BaseVolumeBarAggregator:
    def __init__(self, buf_size: int, reference_cutoff: float):
        self.buf_size = buf_size
        self.reference_cutoff = reference_cutoff
        self.bars = [None] * buf_size
        self.reference_index = 0
        self.finished_bars = 0

    def reset(self):
        self.reference_index = 0
        self.finished_bars = 0
        self.bars = [None] * self.buf_size

    def on_trade(self, trade: Trade):
        while abs(trade.quantity) > 2 * 1e-13: # python's float precision is estimated to 15-17 digits
            need = self.reference_cutoff - self._accumulator % self.reference_cutoff
            next_reference_index = int(self._accumulator // self.reference_cutoff)
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
                self._accumulator += need + 1e-13
            else:
                logger.error(f"Undefined behavior: {self._accumulator=} and {trade.quantity=} and {need=}")


class QuoteVolumeBarAggregator:
    def __init__(self, buf_size: int, reference_cutoff: float):
        self.buf_size = buf_size
        self.reference_cutoff = reference_cutoff
        self.bars = [None] * buf_size
        self.reference_index = 0
        self.finished_bars = 0

    def reset(self):
        self.reference_index = 0
        self.finished_bars = 0
        self.bars = [None] * self.buf_size

    def on_trade(self, trade: Trade):
        while abs(trade.quantity) > 2 * 1e-13: # python's float precision is estimated to 15-17 digits
            need_quote = self.reference_cutoff - self._accumulator % self.reference_cutoff
            need = need_quote / trade.price
            next_reference_index = int(self._accumulator // self.reference_cutoff)
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
                logger.info(f"Finished {self._finished_bars}'th quote volume bar: {bar}")
                self._accumulator += need * trade.price + 1e-13
                self._reference_index += 1
                trade.quantity = 0
            elif trade.quantity < need:
                if bar := self.bars[self._reference_index % self.buf_size]:
                    bar += trade
                else:
                    bar = Bar.from_trade(trade)
                    self.bars[self._reference_index % self.buf_size] = bar
                self._accumulator += trade.quantity * trade.price
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
                logger.info(f"Finished {self._finished_bars}'th quote volume bar: {bar}")
                trade.quantity -= need
                self._accumulator += need * trade.price + 1e-13
            else:
                logger.error(f"Undefined behavior: {self._accumulator=} and {trade.quantity=} and {need_quote=} and {need=}")