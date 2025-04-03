import argparse
import pandas as pd
import datetime as dt
from redis import Redis
from solvexity.helper import to_ms_interval
from solvexity.analytic.feed import Feed
from solvexity.analytic.pattern import Pattern
import yaml

if __name__ == "__main__":
    # Usage: python -m script.generate_features [--symbol SYMBOL] [--start START_DATE] [--end END_DATE] [--config CONFIG_PATH] [--output OUTPUT_PATH]
    # Example: python -m script.generate_features --symbol BTCUSDT --start 2022-03-01 --end 2025-03-29 --config config/pattern.yml --output notebook/data/feature_extraction.csv
    # 
    # Arguments:
    #   --start     Start date in YYYY-MM-DD format (default: 2022-03-01)
    #   --end       End date in YYYY-MM-DD format (default: 2025-03-29)
    #   --step      Step size (default: 1d)
    #   --config    Config file path (default: config/pattern.yml)
    #   --output    Output file path (default: notebook/data/feature_extraction.csv)
    
    
    parser = argparse.ArgumentParser(description='Generate features for crypto data')
    parser.add_argument('--start', type=str, default='2022-03-01', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, default='2025-03-29', help='End date (YYYY-MM-DD)')
    parser.add_argument('--step', type=str, default='1d', help='step size (default: 1d)')
    parser.add_argument('--config', type=str, default='config/pattern.yml', help='Config file path')
    parser.add_argument('--output', type=str, default='notebook/data/feature_extraction.csv', help='Output file path')
    args = parser.parse_args()

    redis_client = Redis(host='localhost', port=6379, db=0)
    # sql_engine = create_engine(os.getenv("SQL_URL"))
    feed = Feed(redis_client)
    pattern = Pattern(feed)
    records = []
    
    with open(args.config, "r") as f:
        config = yaml.safe_load(f)
        
    start_time = dt.datetime.strptime(args.start, "%Y-%m-%d", tzinfo=dt.timezone.utc) # span end time
    end_time = dt.datetime.strptime(args.end, "%Y-%m-%d", tzinfo=dt.timezone.utc)
    step_size = to_ms_interval(args.step)
    feature_map = {}
    while start_time < end_time:
        record = {"timestamp": int(start_time.timestamp() * 1000)}
        print(f"Processing {start_time}")
        for pat in config["patterns"]:
            name = pat["name"]
            print(f"Calculating features for {name}")
            span_end_time = int(start_time.timestamp() * 1000)
            if pat["type"] == "returns":
                span_start_time = int(span_end_time - to_ms_interval(pat["interval"]) * pat["lookback"])
                symbol = pat["symbol"]
                record[name] = pattern.calc_returns(symbol, pat["interval"], span_start_time, span_end_time)
            elif pat["type"] == "volatility":
                span_start_time = int(span_end_time - to_ms_interval(pat["interval"]) * pat["lookback"])
                symbol = pat["symbol"]
                record[name] = pattern.calc_volatility(symbol, pat["interval"], span_start_time, span_end_time)
            elif pat["type"] == "mdd":
                span_start_time = int(span_end_time - to_ms_interval(pat["interval"]) * pat["lookback"])
                symbol = pat["symbol"]
                record[name] = pattern.calc_mdd(symbol, pat["interval"], span_start_time, span_end_time)
            elif pat["type"] == "skewness":
                span_start_time = int(span_end_time - to_ms_interval(pat["interval"]) * pat["lookback"])
                symbol = pat["symbol"]
                record[name] = pattern.calc_skewness(symbol, pat["interval"], span_start_time, span_end_time)
            elif pat["type"] == "kurtosis":
                span_start_time = int(span_end_time - to_ms_interval(pat["interval"]) * pat["lookback"])
                symbol = pat["symbol"]
                record[name] = pattern.calc_kurtosis(symbol, pat["interval"], span_start_time, span_end_time)
            else:
                raise ValueError(f"Invalid pattern type: {pat['type']}")
        
        records.append(record)
        start_time += step_size
    df = pd.DataFrame(records)
    df.to_csv(args.output, index=False)