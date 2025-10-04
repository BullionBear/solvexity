import argparse
import logging
import pandas as pd
from solvexity.strategy.pipeline.analytics import Analytics, DataframeAnalytics


logger = logging.getLogger(__name__)

def calc_returns(df: pd.DataFrame) -> pd.DataFrame:
    df["close"]
    return df

def main(input_path: str, output_path: str):
    logger.info(f"Reading input file from {input_path}")
    df_input = pd.read_csv(input_path)
    df_analytics = DataframeAnalytics(
        [
            Analytics(name="returns", func=lambda x: x["returns"], result_to="returns"),
        ]
    )
    df_output = df_analytics.on_dataframe(df_input)
    logger.info(f"Writing output file to {output_path}")
    df_output.to_csv(output_path, index=False)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Feature Engineering")
    parser.add_argument("--input", type=str, required=True, help="Input file path")
    parser.add_argument("--output", type=str, required=True, help="Output file path")
    args = parser.parse_args()
    main(args.input, args.output)



