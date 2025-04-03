import argparse
import pandas as pd
import datetime as dt
import sys
from redis import Redis
from solvexity.helper import to_ms_interval
from solvexity.analytic.feed import Feed
from solvexity.analytic.pattern import Pattern
from solvexity.config.loader import load_config
from solvexity.config.models import IndicatorType

if __name__ == "__main__":
    # Usage: python -m solvexity.script.generate_features [--start START_DATE] [--end END_DATE] [--step STEP_SIZE] [--config CONFIG_PATH] [--output OUTPUT_PATH]
    # Example: python -m solvexity.script.generate_features --start 2022-03-01 --end 2025-03-29 --step 1d --config config/indicators.yml --output ./feature_extraction.csv
    # 
    # Arguments:
    #   --start     Start date in YYYY-MM-DD format (default: 2022-03-01)
    #   --end       End date in YYYY-MM-DD format (default: 2025-03-29)
    #   --step      Step size (default: 1d)
    #   --config    Config file path (default: config/indicators.yml)
    #   --output    Output file path (default: ./feature_extraction.csv)
    
    
    parser = argparse.ArgumentParser(description='Generate features for crypto data')
    parser.add_argument('--start', type=str, default='2022-03-01', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, default='2025-03-29', help='End date (YYYY-MM-DD)')
    parser.add_argument('--step', type=str, default='1d', help='step size (default: 1d)')
    parser.add_argument('--config', type=str, default='config/indicators.yml', help='Config file path')
    parser.add_argument('--output', type=str, default='./feature_extraction.csv', help='Output file path')
    args = parser.parse_args()

    redis_client = Redis(host='localhost', port=6379, db=0)
    feed = Feed(redis_client)
    pattern: Pattern = Pattern(feed)
    records = []
    
    # Load and validate configuration
    try:
        config = load_config(args.config)
    except Exception as e:
        print(f"Error loading configuration: {e}")
        sys.exit(1)
    
    # Parse dates with proper timezone handling
    try:
        start_time = dt.datetime.strptime(args.start, "%Y-%m-%d")
        start_time = start_time.replace(tzinfo=dt.timezone.utc)
        
        end_time = dt.datetime.strptime(args.end, "%Y-%m-%d")
        end_time = end_time.replace(tzinfo=dt.timezone.utc)
    except ValueError as e:
        print(f"Error parsing dates: {e}")
        sys.exit(1)
        
    step_size = dt.timedelta(milliseconds=to_ms_interval(args.step))
    
    while start_time < end_time:
        record = {"timestamp": int(start_time.timestamp() * 1000)}
        print(f"Processing {start_time}")
        
        # Process lookback indicators
        for indicator in config.indicators.lookback:
            name = indicator.name
            print(f"Calculating lookback features for {name}")
            
            span_end_time = int(start_time.timestamp() * 1000)
            span_start_time = int(span_end_time - to_ms_interval(indicator.interval.value) * indicator.period)
            
            # Calculate indicator based on type
            if indicator.type == IndicatorType.RETURNS:
                record[name] = pattern.calc_returns(
                    indicator.symbol, 
                    indicator.interval.value, 
                    span_start_time, 
                    span_end_time
                )
            elif indicator.type == IndicatorType.VOLATILITY:
                record[name] = pattern.calc_volatility(
                    indicator.symbol, 
                    indicator.interval.value, 
                    span_start_time, 
                    span_end_time
                )
            elif indicator.type == IndicatorType.MDD:
                record[name] = pattern.calc_mdd(
                    indicator.symbol, 
                    indicator.interval.value, 
                    span_start_time, 
                    span_end_time
                )
            elif indicator.type == IndicatorType.SKEWNESS:
                record[name] = pattern.calc_skewness(
                    indicator.symbol, 
                    indicator.interval.value, 
                    span_start_time, 
                    span_end_time
                )
            elif indicator.type == IndicatorType.KURTOSIS:
                record[name] = pattern.calc_kurtosis(
                    indicator.symbol, 
                    indicator.interval.value, 
                    span_start_time, 
                    span_end_time
                )
        
        # Process lookafter indicators
        for indicator in config.indicators.lookafter:
            name = indicator.name
            print(f"Calculating lookafter features for {name}")
            
            span_start_time = int(start_time.timestamp() * 1000)
            span_end_time = int(span_start_time + to_ms_interval(indicator.interval.value) * indicator.period)
            
            if indicator.type == IndicatorType.STOPPING_RETURN:
                record[name] = pattern.stopping_return(
                    indicator.symbol, 
                    indicator.interval.value, 
                    span_start_time, 
                    span_end_time, 
                    indicator.stop_loss, 
                    indicator.stop_profit
                )
        
        records.append(record)
        start_time += step_size
    
    df = pd.DataFrame(records)
    df.to_csv(args.output, index=False)
    print(f"Features saved to {args.output}")