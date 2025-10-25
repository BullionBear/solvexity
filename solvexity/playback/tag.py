import argparse
from solvexity.logging import setup_logging
import logging
from solvexity.playback.serde.iterator import TradeIterator
from solvexity.playback.serde.metadata import MetadataWriter

setup_logging()
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', type=str, required=True)
    parser.add_argument('-o', '--output', type=str, required=True)
    args = parser.parse_args()

    logger.info(f"Input: {args.input}")
    logger.info(f"Output: {args.output}")

    trade_iterator = TradeIterator()
    metadata_writer = MetadataWriter(args.input)
    for trade in trade_iterator.replay_from_files([args.input]):
        metadata_writer.on_trade(trade)

    with open(args.output, 'w') as f:
        logger.info(f"Writing metadata to {args.output}")
        f.write(metadata_writer.to_json())

if __name__ == '__main__':
    main()