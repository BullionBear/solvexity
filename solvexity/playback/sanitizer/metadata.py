from solvexity.model import Exchange, Instrument, Symbol, Trade
from pydantic import BaseModel
from collections import defaultdict
import hashlib
import json


class Segment(BaseModel):
    exchange: Exchange
    instrument: Instrument
    symbol: Symbol
    start_id: int
    end_id: int
    start_time: int
    end_time: int
    total_volume: float
    total_quote_volume: float
    total_trades: int

    @classmethod
    def from_trade(cls, trade: Trade) -> 'Segment':
        segment = cls(
            exchange=trade.exchange,
            instrument=trade.instrument,
            symbol=trade.symbol,
            start_id=trade.id,
            end_id=trade.id,
            start_time=trade.timestamp,
            end_time=trade.timestamp,
            total_volume=trade.quantity,
            total_quote_volume=trade.price * trade.quantity,
            total_trades=1
        )
        return segment

    def __radd__(self, other: Trade) -> 'Segment':
        return self.__iadd__(other)
    
    def __iadd__(self, other: Trade) -> 'Segment':
        self.end_id = other.id
        self.total_volume += other.quantity
        self.total_quote_volume += other.price * other.quantity
        self.total_trades += 1
        self.end_time = other.timestamp
        return self
    

class MetadataWriter:
    def __init__(self, file_path: str):
        self.file_path = file_path
        with open(file_path, 'rb') as f:
            self.md5 = hashlib.md5(f.read()).hexdigest()
        self.segments: dict[tuple[Exchange, Instrument, Symbol], list[Segment]] = defaultdict(list)
        self.n_total = 0

    def on_trade(self, trade: Trade):
        key = (trade.exchange, trade.instrument, trade.symbol)
        if len(self.segments[key]) == 0:
            self.segments[key].append(Segment.from_trade(trade))
        elif self.segments[key][-1].end_id + 1 == trade.id:
            self.segments[key][-1] += trade
        else:
            self.segments[key].append(Segment.from_trade(trade))
        self.n_total += 1

    def to_json(self) -> str:
        segments = []
        for segment_list in self.segments.values():
            for segment in segment_list:
                segments.append(segment.model_dump())
        return json.dumps({
            "file": self.file_path,
            "md5": self.md5,
            "segments": segments
        }, indent=2)