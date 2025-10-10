from collections import deque
from abc import ABC, abstractmethod
from typing import Literal
from pydantic import BaseModel
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

    @classmethod
    def from_str(cls, bar_type: str) -> 'BarType':
        if bar_type == "time":
            return cls.TIME
        elif bar_type == "tick":
            return cls.TICK
        elif bar_type == "base_volume":
            return cls.BASE_VOLUME
        elif bar_type == "quote_volume":
            return cls.QUOTE_VOLUME
        else:
            raise ValueError(f"Unknown bar type: {bar_type}")

class TradeStatus(Enum):
    ACCEPTED = "accepted"
    BYPASS = "bypass"
    MISSING = "missing"

class Interval(BaseModel):
    start_id: int
    end_id: int

    @property
    def n_trades(self) -> int:
        return self.end_id - self.start_id

class AggregatorFactory:
    @classmethod
    def from_dict(cls, bar_type: BarType, data: dict) -> 'BarAggregator':
        logger.info(f"Creating aggregator from dict: {bar_type}")
        if bar_type == BarType.TIME:
            return TimeBarAggregator.from_dict(data)
        elif bar_type == BarType.TICK:
            return TickBarAggregator.from_dict(data)
        elif bar_type == BarType.BASE_VOLUME:
            return BaseVolumeBarAggregator.from_dict(data)
        elif bar_type == BarType.QUOTE_VOLUME:
            return QuoteVolumeBarAggregator.from_dict(data)
        else:
            raise ValueError(f"Unknown aggregator type: {bar_type}")

class BarAggregator(ABC):
    def __init__(self, buf_size: int, reference_cutoff: int, completeness_threshold: float = 1.0):
        self.buf_size = buf_size
        self.reference_cutoff = reference_cutoff
        self.bars: deque[Bar] = deque(maxlen=buf_size)
        
        self.completeness_threshold = completeness_threshold
        self.missing_trades = 0
        self.missing_intervals: deque[Interval] = deque(maxlen=buf_size)

    def to_dict(self) -> dict:
        return {
            "buf_size": self.buf_size,
            "reference_cutoff": self.reference_cutoff,
            "bars": [bar.model_dump() for bar in self.bars],

            "completeness_threshold": self.completeness_threshold,
            "missing_trades": self.missing_trades,
            "missing_intervals": [interval.model_dump() for interval in self.missing_intervals],
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'BarAggregator':
        aggregator = cls(data["buf_size"], data["reference_cutoff"], data["completeness_threshold"])
        for bar in data["bars"]:
            aggregator.bars.append(Bar.model_validate(bar))
        aggregator.missing_trades = data["missing_trades"]
        for interval in data["missing_intervals"]:
            aggregator.missing_intervals.append(Interval.model_validate(interval))
        return aggregator

    def reset(self):
        self.bars.clear()
        self.missing_intervals.clear()
        self.missing_trades = 0

    def validate(self, trade: Trade) -> TradeStatus:
        if len(self.bars) == 0:
            return TradeStatus.ACCEPTED
        if self.bars[-1].next_id == trade.id:
            return TradeStatus.ACCEPTED
        if self.bars[-1].next_id > trade.id:
            return TradeStatus.BYPASS
        logger.warning(f"Missing trade from {self.bars[-1].next_id} to {trade.id}")
        interval = Interval(start_id=self.bars[-1].next_id, end_id=trade.id)
        self.missing_intervals.append(interval)
        self.missing_trades += interval.n_trades
        self._correct_missing_intervals()
        return TradeStatus.MISSING

    def _correct_missing_intervals(self):
        if len(self.bars) == 0 or len(self.missing_intervals) == 0:
            return
        while len(self.missing_intervals) > 0 and self.bars[0].start_id > self.missing_intervals[0].start_id:
            self.missing_trades -= self.missing_intervals[0].n_trades
            self.missing_intervals.popleft()
    
    def is_valid(self) -> bool:
        if len(self.bars) == 0:
            return True
        n_total_trades = self.bars[-1].next_id - self.bars[0].start_id
        if abs(self.missing_trades - n_total_trades * self.completeness_threshold) <= 1e-13:
            return True
        logger.warning(f"Invalid completeness: {self.missing_trades=} and {n_total_trades=} and {self.completeness_threshold=}")
        return False

    @abstractmethod
    def on_trade(self, trade: Trade):
        pass

    def size(self) -> int:
        return len(self.bars)
    
    def last(self, is_closed: bool = True) -> Bar | None:
        if len(self.bars) <= 1:
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
    def __init__(self, buf_size: int, reference_cutoff: int, completeness_threshold: float = 1.0):
        super().__init__(buf_size, reference_cutoff, completeness_threshold)
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
        status = self.validate(trade)
        if status == TradeStatus.MISSING:
            if not self.is_valid():
                self.reset()
        if status == TradeStatus.BYPASS:
            return
        # else status == TradeStatus.ACCEPTED
        
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
            logger.warning(f"Invalid reference index: {prev_reference_index} and next reference index: {next_reference_index}")
    
    

class TickBarAggregator(BarAggregator):
    def __init__(self, buf_size: int, reference_cutoff: int, completeness_threshold: float = 1.0):
        super().__init__(buf_size, reference_cutoff, completeness_threshold)
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
        status = self.validate(trade)
        if status == TradeStatus.MISSING:
            if not self.is_valid():
                self.reset()
        if status == TradeStatus.BYPASS:
            return
        # else status == TradeStatus.ACCEPTED

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
            logger.warning(f"Invalid reference index: {prev_reference_index} and next reference index: {next_reference_index}")
    


class BaseVolumeBarAggregator(BarAggregator):
    def __init__(self, buf_size: int, reference_cutoff: float, completeness_threshold: float = 1.0):
        super().__init__(buf_size, reference_cutoff, completeness_threshold)
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
        status = self.validate(trade)
        if status == TradeStatus.MISSING:
            if not self.is_valid():
                self.reset()
        if status == TradeStatus.BYPASS:
            return
        # else status == TradeStatus.ACCEPTED
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
                logger.warning(f"Undefined behavior: {self.accumulator=} and {trade.quantity=} and {need=}")
                break


class QuoteVolumeBarAggregator(BarAggregator):
    def __init__(self, buf_size: int, reference_cutoff: float, completeness_threshold: float = 1.0):
        super().__init__(buf_size, reference_cutoff, completeness_threshold)
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
        status = self.validate(trade)
        if status == TradeStatus.MISSING:
            if not self.is_valid():
                self.reset()
        if status == TradeStatus.BYPASS:
            return
        # else status == TradeStatus.ACCEPTED
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
                logger.warning(f"Undefined behavior: {self.accumulator=} and {trade.quantity=} and {need_quote=}, {need_base=}")
                break
