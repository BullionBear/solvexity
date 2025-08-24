#!/usr/bin/env python3
"""
Max Drawdown Analysis Script

This script fetches 5-minute kline data from Binance API for the period 2025-01-01 to 2025-01-07,
converts the data to Bar objects, calculates the maximum drawdown considering high-low relationships,
and finds the drawdown range.
"""

import asyncio
import pandas as pd
import logging
from datetime import datetime, timezone
from typing import List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

# Import from the existing codebase
from solvexity.connector.binance.rest import BinanceRestClient
from solvexity.strategy.model.bar import Bar
from solvexity.strategy.model.enum import Symbol, Exchange

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Interval(Enum):
    """Kline intervals"""
    ONE_MINUTE = "1m"
    FIVE_MINUTES = "5m"
    FIFTEEN_MINUTES = "15m"
    THIRTY_MINUTES = "30m"
    ONE_HOUR = "1h"
    FOUR_HOURS = "4h"
    ONE_DAY = "1d"


@dataclass
class DrawdownResult:
    """Result of drawdown calculation"""
    max_drawdown: float
    start_index: int
    end_index: int
    start_price: float
    end_price: float
    peak_price: float


class MaxDrawdownAnalyzer:
    """Analyzer for calculating maximum drawdown with high-low relationship consideration"""
    
    def __init__(self, symbol: str = "BTCUSDT"):
        self.symbol = symbol
        self.client = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.client = BinanceRestClient()
        await self.client.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.client:
            await self.client.__aexit__(exc_type, exc_val, exc_tb)
    
    def _timestamp_to_ms(self, dt: datetime) -> int:
        """Convert datetime to milliseconds timestamp"""
        return int(dt.replace(tzinfo=timezone.utc).timestamp() * 1000)
    
    def _ms_to_datetime(self, ms: int) -> datetime:
        """Convert milliseconds timestamp to datetime"""
        return datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
    
    def _parse_kline_to_bar(self, kline: List[float]) -> Bar:
        """Convert Binance kline data to Bar object"""
        # Binance kline format: [open_time, open, high, low, close, volume, close_time, quote_volume, ...]
        open_time_ms = int(kline[0])
        close_time_ms = int(kline[6])
        
        return Bar(
            symbol=Symbol(quote="USDT", base="BTC"),  # Simplified for BTCUSDT
            exchange=Exchange.BINANCE,
            interval="5m",
            open_time_ms=open_time_ms,
            open=float(kline[1]),
            high=float(kline[2]),
            low=float(kline[3]),
            close=float(kline[4]),
            volume=float(kline[5]),
            quote_volume=float(kline[7]),
            close_time_ms=close_time_ms
        )
    
    def _determine_price_order(self, bar: Bar) -> str:
        """
        Determine the order of high and low prices within a bar.
        If close - low < high - close, then high happened before low.
        Returns: 'high_first' or 'low_first'
        """
        close_to_low = bar.close - bar.low
        high_to_close = bar.high - bar.close
        
        if close_to_low < high_to_close:
            return 'high_first'
        else:
            return 'low_first'
    
    def _bars_to_dataframe(self, bars: List[Bar]) -> pd.DataFrame:
        """Convert list of Bar objects to pandas DataFrame"""
        data = []
        for i, bar in enumerate(bars):
            price_order = self._determine_price_order(bar)
            data.append({
                'index': i,
                'timestamp': self._ms_to_datetime(bar.open_time_ms),
                'open_time_ms': bar.open_time_ms,
                'open': bar.open,
                'high': bar.high,
                'low': bar.low,
                'close': bar.close,
                'volume': bar.volume,
                'quote_volume': bar.quote_volume,
                'price_order': price_order,
                # For drawdown calculation, we need to consider the price order
                'effective_high': bar.high if price_order == 'high_first' else bar.close,
                'effective_low': bar.close if price_order == 'high_first' else bar.low,
            })
        
        return pd.DataFrame(data)
    
    def _calculate_max_drawdown(self, df: pd.DataFrame) -> DrawdownResult:
        """
        Calculate maximum drawdown considering the high-low relationship within each bar.
        
        The algorithm:
        1. For each bar, determine if high or low came first based on price relationship
        2. Use the appropriate price (high if high came first, close if low came first) for peak calculation
        3. Use the appropriate price (close if high came first, low if low came first) for trough calculation
        4. Calculate running maximum and drawdown
        """
        if df.empty:
            raise ValueError("DataFrame is empty")
        
        # Initialize variables
        running_max = df['effective_high'].iloc[0]
        max_drawdown = 0.0
        
        peak_index = 0
        trough_index = 0
        peak_price = running_max
        trough_price = df['effective_low'].iloc[0]
        
        # Track the peak that occurred before the current trough
        current_peak_index = 0
        current_peak_price = running_max
        
        for i in range(1, len(df)):
            current_high = df['effective_high'].iloc[i]
            current_low = df['effective_low'].iloc[i]
            
            # Update running maximum if we have a new peak
            if current_high > running_max:
                running_max = current_high
                current_peak_index = i
                current_peak_price = current_high
            
            # Calculate current drawdown from the running maximum
            current_drawdown = (running_max - current_low) / running_max
            
            # Update maximum drawdown if current drawdown is larger
            if current_drawdown > max_drawdown:
                max_drawdown = current_drawdown
                peak_index = current_peak_index  # Use the peak that occurred before this trough
                trough_index = i
                peak_price = current_peak_price
                trough_price = current_low
        
        # If no drawdown was found, return 0
        if max_drawdown == 0.0:
            return DrawdownResult(
                max_drawdown=0.0,
                start_index=0,
                end_index=0,
                start_price=df['effective_high'].iloc[0],
                end_price=df['effective_low'].iloc[0],
                peak_price=df['effective_high'].iloc[0]
            )
        
        return DrawdownResult(
            max_drawdown=max_drawdown,
            start_index=peak_index,
            end_index=trough_index,
            start_price=peak_price,
            end_price=trough_price,
            peak_price=peak_price
        )
    
    async def fetch_and_analyze(self, start_date: str = "2025-01-01", end_date: str = "2025-01-07") -> Tuple[pd.DataFrame, DrawdownResult]:
        """
        Fetch kline data and perform max drawdown analysis
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            Tuple of (DataFrame, DrawdownResult)
        """
        # Parse dates
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Convert to milliseconds
        start_time_ms = self._timestamp_to_ms(start_dt)
        end_time_ms = self._timestamp_to_ms(end_dt)
        
        logger.info(f"Fetching 5m kline data for {self.symbol} from {start_date} to {end_date}")
        logger.info(f"Start time: {start_time_ms} ({start_dt})")
        logger.info(f"End time: {end_time_ms} ({end_dt})")
        
        # Fetch kline data
        klines = await self.client.get_klines(
            symbol=self.symbol,
            interval=Interval.FIVE_MINUTES.value,
            start_time=start_time_ms,
            end_time=end_time_ms
        )
        
        logger.info(f"Fetched {len(klines)} klines")
        
        # Convert klines to Bar objects
        bars = [self._parse_kline_to_bar(kline) for kline in klines]
        logger.info(f"Converted to {len(bars)} Bar objects")
        
        # Convert to DataFrame
        df = self._bars_to_dataframe(bars)
        logger.info(f"Converted to DataFrame with {len(df)} rows")
        
        # Calculate max drawdown
        drawdown_result = self._calculate_max_drawdown(df)
        
        return df, drawdown_result
    
    def print_analysis_results(self, df: pd.DataFrame, result: DrawdownResult):
        """Print detailed analysis results"""
        print("\n" + "="*60)
        print("MAX DRAWDOWN ANALYSIS RESULTS")
        print("="*60)
        
        print(f"Symbol: {self.symbol}")
        print(f"Period: {df['timestamp'].iloc[0]} to {df['timestamp'].iloc[-1]}")
        print(f"Total bars: {len(df)}")
        
        print(f"\nMax Drawdown: {result.max_drawdown:.4f} ({result.max_drawdown*100:.2f}%)")
        print(f"Peak Price: {result.peak_price:.2f}")
        print(f"Trough Price: {result.end_price:.2f}")
        print(f"Price Drop: {result.peak_price - result.end_price:.2f}")
        
        print(f"\nDrawdown Range:")
        print(f"  Start Index: {result.start_index}")
        print(f"  End Index: {result.end_index}")
        print(f"  Duration: {result.end_index - result.start_index + 1} bars")
        
        if result.start_index < len(df) and result.end_index < len(df):
            start_time = df['timestamp'].iloc[result.start_index]
            end_time = df['timestamp'].iloc[result.end_index]
            print(f"  Start Time: {start_time}")
            print(f"  End Time: {end_time}")
        
        print(f"\nPrice Order Analysis:")
        high_first_count = len(df[df['price_order'] == 'high_first'])
        low_first_count = len(df[df['price_order'] == 'low_first'])
        print(f"  Bars with High First: {high_first_count} ({high_first_count/len(df)*100:.1f}%)")
        print(f"  Bars with Low First: {low_first_count} ({low_first_count/len(df)*100:.1f}%)")


async def main():
    """Main function to run the analysis"""
    symbol = "BTCUSDT"
    start_date = "2025-01-01"
    end_date = "2025-01-07"
    
    async with MaxDrawdownAnalyzer(symbol) as analyzer:
        try:
            # Fetch and analyze data
            df, drawdown_result = await analyzer.fetch_and_analyze(start_date, end_date)
            
            # Print results
            analyzer.print_analysis_results(df, drawdown_result)
            
            # Save DataFrame to CSV for inspection
            output_file = f"max_drawdown_analysis_{symbol}_{start_date}_{end_date}.csv"
            df.to_csv(output_file, index=False)
            print(f"\nDataFrame saved to: {output_file}")
            
        except Exception as e:
            logger.error(f"Error during analysis: {e}")
            raise


if __name__ == "__main__":
    # Run the analysis
    asyncio.run(main())
