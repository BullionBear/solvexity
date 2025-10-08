from collections import deque
from abc import ABC, abstractmethod
from typing import TextIO
from solvexity.model.trade import Trade
from solvexity.model.bar import Bar
from enum import Enum
import logging
import pandas as pd
import json

logger = logging.getLogger(__name__)

class BarType(Enum):
    TIME = "time"
    TICK = "tick"
    BASE_VOLUME = "base_volume"
    QUOTE_VOLUME = "quote_volume"

class BarAggregator(ABC):
    def __init__(self, buf_size: int, reference_cutoff: int):
        self.buf_size = buf_size
        self.reference_cutoff = reference_cutoff
        self.bars: deque[Bar] = deque(maxlen=buf_size)

    def to_dict(self) -> dict:
        return {
            "buf_size": self.buf_size,
            "reference_cutoff": self.reference_cutoff,
            "bars": [bar.model_dump() for bar in self.bars]
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'BarAggregator':
        aggregator = cls(data["buf_size"], data["reference_cutoff"])
        for bar in data["bars"]:
            aggregator.bars.append(Bar.model_validate(bar))
        return aggregator

    def reset(self):
        self.bars.clear()

    @abstractmethod
    def on_trade(self, trade: Trade):
        pass

    def size(self) -> int:
        return len(self.bars)
    
    def last(self, is_closed: bool = True) -> Bar | None:
        if len(self.bars) <= 2:
            return None
        if is_closed:
            for bar in reversed(self.bars):
                if bar.is_closed:
                    return bar
            return None
        else:
            return self.bars[-1]
    
    def to_dataframe(self, is_closed: bool = True) -> pd.DataFrame:
        if is_closed:
            df = pd.DataFrame([bar.model_dump_flatten() for bar in reversed(self.bars) if bar.is_closed])
        else:
            df = pd.DataFrame([bar.model_dump_flatten() for bar in reversed(self.bars)])
        df = df.iloc[::-1].reset_index(drop=True)
        return df

class TimeBarAggregator(BarAggregator):
    def __init__(self, buf_size: int, reference_cutoff: int):
        super().__init__(buf_size, reference_cutoff)
        self.accumulator = 0

    def to_dict(self) -> dict:
        data = super().to_dict()
        data["accumulator"] = self.accumulator
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'TimeBarAggregator':
        obj = super(TimeBarAggregator, cls).from_dict(data)
        obj.accumulator = data["accumulator"]
        return obj

    def reset(self):
        super().reset()
        self.accumulator = 0


    def on_trade(self, trade: Trade):
        self.accumulator = trade.timestamp
        if len(self.bars) == 0:
            self.bars.append(Bar.from_trade(trade))
            self.bars[-1].open_time = self.accumulator // self.reference_cutoff * self.reference_cutoff
            return
        prev_reference_index = self.bars[-1].open_time // self.reference_cutoff
        next_reference_index = int(self.accumulator // self.reference_cutoff)
        # logger.info(f"prev_reference_index: {prev_reference_index}, next_reference_index: {next_reference_index}")
        if prev_reference_index == next_reference_index:
            self.bars[-1] += trade
            # logger.info(f"Add time bar: {self.bars[-1]}")
        elif next_reference_index > prev_reference_index:
            self.bars[-1].enclose(next_reference_index * self.reference_cutoff - 1)
            logger.info(f"Enclose time bar: {self.bars[-1]}")
            self.bars.append(Bar.from_trade(trade))
            self.bars[-1].open_time = next_reference_index * self.reference_cutoff
        else:
            self.reset()
            logger.error(f"Invalid reference index: {prev_reference_index} and next reference index: {next_reference_index}")
    
    

class TickBarAggregator(BarAggregator):
    def __init__(self, buf_size: int, reference_cutoff: int):
        super().__init__(buf_size, reference_cutoff)
        self.accumulator = 0

    def to_dict(self) -> dict:
        data = super().to_dict()
        data["accumulator"] = self.accumulator
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'TickBarAggregator':
        obj = super(TickBarAggregator, cls).from_dict(data)
        obj.accumulator = data["accumulator"]
        return obj

    def reset(self):
        super().reset()
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
    


class BaseVolumeBarAggregator(BarAggregator):
    def __init__(self, buf_size: int, reference_cutoff: float):
        super().__init__(buf_size, reference_cutoff)
        self.accumulator = 0

    def to_dict(self) -> dict:
        data = super().to_dict()
        data["accumulator"] = self.accumulator
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'BaseVolumeBarAggregator':
        obj = super(BaseVolumeBarAggregator, cls).from_dict(data)
        obj.accumulator = data["accumulator"]
        return obj

    def reset(self):
        super().reset()
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


class QuoteVolumeBarAggregator(BarAggregator):
    def __init__(self, buf_size: int, reference_cutoff: float):
        super().__init__(buf_size, reference_cutoff)
        self.accumulator = 0

    def to_dict(self) -> dict:
        data = super().to_dict()
        data["accumulator"] = self.accumulator
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'QuoteVolumeBarAggregator':
        obj = super(QuoteVolumeBarAggregator, cls).from_dict(data)
        obj.accumulator = data["accumulator"]
        return obj

    def reset(self):
        super().reset()
        self.accumulator = 0

    def on_trade(self, trade: Trade):
        while abs(trade.quantity) > 2 * 1e-13: # python's float precision is estimated to 15-17 digits
            if len(self.bars) == 0 or self.bars[-1].is_closed:
                empty_trade = trade.model_copy(deep=False)
                empty_trade.quantity = 0
                self.bars.append(Bar.from_trade(empty_trade))

            need_quote = self.reference_cutoff - self.accumulator % self.reference_cutoff
            need_base = need_quote / trade.price
            if abs(trade.quantity - need_base) < 2 * 1e-13: # trade.quantity = need_base               
                self.bars[-1] += trade
                self.bars[-1].enclose(trade.timestamp)
                logger.info(f"Enclose quote volume bar: {self.bars[-1]} with {trade.quantity=} ~ {need_base=}")
                self.accumulator += need_quote + 1e-13
                trade.quantity = 0
            elif trade.quantity < need_base:
                self.bars[-1] += trade
                self.accumulator += trade.quantity * trade.price
                trade.quantity = 0
            elif trade.quantity > need_base:
                trade_fraction = trade.model_copy(deep=False)
                trade_fraction.quantity = need_base
                self.bars[-1] += trade_fraction
                self.bars[-1].enclose(trade_fraction.timestamp)
                self.bars[-1].next_id = trade_fraction.id
                logger.info(f"Enclose quote volume bar: {self.bars[-1]} with {trade.quantity=} > {need_base=}")
                self.accumulator += need_quote + 1e-13
                trade.quantity -= trade_fraction.quantity
            else:
                self.reset()
                logger.error(f"Undefined behavior: {self.accumulator=} and {trade.quantity=} and {need_quote=}, {need_base=}")
                break
