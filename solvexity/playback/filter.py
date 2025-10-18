import argparse
from solvexity.logging import setup_logging
import json
import logging
from solvexity.playback.sanitizer.iterator import TradeIterator
from solvexity.playback.sanitizer.metadata import MetadataWriter
from solvexity.model import Trade, Symbol, Exchange, Instrument

setup_logging()
logger = logging.getLogger(__name__)

class Validator:
    def __init__(self, exchanges: list[Exchange], instruments: list[Instrument], symbols: list[Symbol], start_ts: int, end_ts: int):
        self.exchanges = exchanges
        self.instruments = instruments
        self.symbols = symbols
        self.start_ts = start_ts
        self.end_ts = end_ts
    
    def is_trade_valid(self, trade: Trade) -> bool:
        if self.exchanges and trade.exchange not in self.exchanges:
            return False
        if self.instruments and trade.instrument not in self.instruments:
            return False
        if self.symbols and trade.symbol not in self.symbols:
            return False
        if self.start_ts and trade.timestamp < self.start_ts:
            return False
        if self.end_ts and trade.timestamp > self.end_ts:
            return False
        return True




def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--inputs', type=str, required=True, nargs='+')
    parser.add_argument('-e', '--exchanges', type=int, required=True)
    parser.add_argument('-t', '--instruments', type=int, required=True)
    parser.add_argument('-s', '--symbols', type=str, required=True)
    parser.add_argument('-d', '--start-ts', type=int, required=False)
    parser.add_argument('-u', '--end-ts', type=int, required=False)
    parser.add_argument('-o', '--output', type=str, required=True)
    args = parser.parse_args()
    logger.info(f"Inputs: {args.inputs}")
    logger.info(f"Exchanges: {args.exchanges}")
    logger.info(f"Instruments: {args.instruments}")
    logger.info(f"Symbols: {args.symbols}")
    logger.info(f"Start TS: {args.start_ts}")
    logger.info(f"End TS: {args.end_ts}")
    logger.info(f"Output: {args.output}")
    for filename in args.inputs:
        with open(filename, 'r') as f:
            metadata = json.load(f)
        logger.info(f"Metadata: {metadata}")
    # Check completeness of metadata in each symbol
    

if __name__ == "__main__":
    main()