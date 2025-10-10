import asyncio
import json
import logging
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import nats
from nats.aio.msg import Msg
from nats.js.api import ConsumerConfig, DeliverPolicy, AckPolicy, ReplayPolicy
from solvexity.strategy.config import OsirisConfig
from solvexity.logging import setup_logging
from solvexity.model.trade import Trade
import solvexity.strategy as strategy
from solvexity.toolbox.aggregator import (
    AggregatorFactory,
    BarType
)
from solvexity.eventbus import EventBus
from solvexity.eventbus.event import Event

setup_logging()

logger = logging.getLogger(__name__)


def signal_handler(shutdown_event: asyncio.Event):
    """Return a signal handler function that sets the shutdown event"""
    def handler(sig, frame):
        logger.info(f"Received signal {sig}, initiating graceful shutdown...")
        shutdown_event.set()
    return handler
    
async def setup_jetstream_consumer(js, config: OsirisConfig, start_time_ms: int = int(time.time() * 1000)):
    """Setup JetStream consumer with proper configuration"""
    try:
        deliver_policy_map = {
            "all": DeliverPolicy.ALL,
            "last": DeliverPolicy.LAST,
            "new": DeliverPolicy.NEW,
            "by_start_sequence": DeliverPolicy.BY_START_SEQUENCE,
            "by_start_time": DeliverPolicy.BY_START_TIME,
            "last_per_subject": DeliverPolicy.LAST_PER_SUBJECT
        }
        
        ack_policy_map = {
            "none": AckPolicy.NONE,
            "all": AckPolicy.ALL,
            "explicit": AckPolicy.EXPLICIT
        }
        
        replay_policy_map = {
            "instant": ReplayPolicy.INSTANT,
            "original": ReplayPolicy.ORIGINAL
        }
        
        # Keep opt_start_time as-is (should be RFC3339 string or None)
        # The NATS server expects RFC3339 format, not datetime or int
        opt_start_time = datetime.fromtimestamp(start_time_ms / 1000, tz=timezone.utc).isoformat()
        
        
        # Create consumer configuration
        consumer_config = ConsumerConfig(
            name=config.consumer.name,
            description=config.consumer.description,
            durable_name=config.consumer.durable_name,
            deliver_policy=deliver_policy_map.get(config.consumer.deliver_policy, DeliverPolicy.BY_START_TIME),
            opt_start_time=opt_start_time,  # Pass the RFC3339 string directly
            ack_policy=ack_policy_map.get(config.consumer.ack_policy, AckPolicy.NONE),
            ack_wait=config.consumer.ack_wait,
            max_deliver=config.consumer.max_deliver,
            filter_subject=config.consumer.filter_subject,
            replay_policy=replay_policy_map.get(config.consumer.replay_policy, ReplayPolicy.INSTANT),
            sample_freq=config.consumer.sample_freq,
            rate_limit_bps=config.consumer.rate_limit_bps,
            max_ack_pending=config.consumer.max_ack_pending,
            idle_heartbeat=config.consumer.idle_heartbeat,
            flow_control=config.consumer.flow_control,
            deliver_subject=config.consumer.deliver_subject,
            deliver_group=config.consumer.deliver_group
        )

        logger.info(f"Consumer config: {consumer_config}")
        
        # Create or update the consumer
        consumer_info = await js.add_consumer(
            stream=config.consumer.stream,
            config=consumer_config
        )
        
        logger.info(f"Created JetStream consumer: {consumer_info.name}")
        return consumer_info
        
    except Exception as e:
        logger.error(f"Failed to create JetStream consumer: {e}")
        raise


async def cleanup_consumer(js, stream_name: str, consumer_name: str):
    """Remove the JetStream consumer on exit"""
    try:
        await js.delete_consumer(stream=stream_name, consumer=consumer_name)
        logger.info(f"Removed JetStream consumer: {consumer_name}")
    except Exception as e:
        logger.error(f"Failed to remove JetStream consumer {consumer_name}: {e}")

async def main(config_path: str = "config/osiris.json"):
    # Load configuration

    shutdown_event = asyncio.Event()
    
    try:
        config = OsirisConfig.from_yaml(config_path)
        logger.info(f"Loaded configuration from: {config_path}")
    except Exception as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler(shutdown_event))
    signal.signal(signal.SIGTERM, signal_handler(shutdown_event))
    with open(config.aggregator.deserialize_from, "r") as f:
        bar_type = BarType.from_str(config.aggregator.type)
        aggregator = AggregatorFactory.from_dict(bar_type, json.load(f))
    
    nc = None
    js = None
    consumer_created = False
    eb = EventBus()
    
    bar_id = 0
    async def on_trade(e: Event):
        aggregator.on_trade(e.data)
        nonlocal bar_id
        if aggregator.size() != aggregator.buf_size:
            return
        if bar := aggregator.last(is_closed=True):
            if bar_id != bar.next_id:
                logger.info(f"New bar: {bar}")
                bar_id = bar.next_id
            else: # same bar
                return
            if bar.close_time < int(time.time() * 1000) - config.alpha.recv_window:
                logger.info(f"Close time {bar.close_time} is less than {int(time.time() * 1000) - config.alpha.recv_window}")
                return
            df = aggregator.to_dataframe(is_closed=True)
            await eb.publish("on_dataframe", Event(data=df))

    eb.subscribe("on_trade", on_trade)

    async def on_dataframe(e: Event):
        df = e.data
        logger.info(f"Dataframe: {df.shape}")
        df["cummax.close"] = df["close"].cummax()
        df["drawdown.close"] = (df["cummax.close"] - df["close"]) / df["cummax.close"]
        drawdown_momentum = np.sum(df["drawdown.close"] ** 2)
        logger.info(f"Drawdown momentum: {drawdown_momentum}")
        df["cummin.close"] = df["close"].cummin()
        df["runup.close"] = (df["close"] - df["cummin.close"]) / df["cummin.close"]
        runup_momentum = np.sum(df["runup.close"] ** 2)
        logger.info(f"Runup momentum: {runup_momentum}")
        ratio = drawdown_momentum / runup_momentum
        logger.info(f"Ratio: {ratio}")
        """
        ref = df.iloc[-1]["close_time"]
        output_path = Path("./artifacts") / f"dataframe_{ref}.csv"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        """

    eb.subscribe("on_dataframe", on_dataframe)
    
    try:
        logger.info(f"Attempting to connect to NATS servers: {config.consumer.nats_url}")
        # Connect to NATS
        nc = await nats.connect(servers=config.consumer.nats_url)
        logger.info("Connected to NATS")
        
        # Get JetStream context
        js = nc.jetstream()
        logger.info("JetStream context created")
        
        # Set up JetStream consumer
        start_time = 0
        if bar := aggregator.last(is_closed=False):
            start_time = bar.open_time
        await setup_jetstream_consumer(js, config, start_time)
        consumer_created = True

        async def trade_handler(msg: Msg):
            trade = Trade.from_protobuf_bytes(msg.data)
            await eb.publish("on_trade", Event(data=trade))
        
        # Subscribe to the fanout subject (push-based consumer)
        await nc.subscribe(config.consumer.deliver_subject, cb=trade_handler)
        logger.info(f"Subscribed to {config.consumer.deliver_subject}")
        
        logger.info("Waiting for trade messages... Press Ctrl+C to stop")
        
        # Wait for shutdown signal instead of infinite loop
        await shutdown_event.wait()
        logger.info("Shutdown signal received, cleaning up...")
        
    except Exception:
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
    finally:
        logger.info("Entering finally block...")
        # Clean up the consumer before closing connection
        if js and consumer_created:
            await cleanup_consumer(js, config.consumer.stream, config.consumer.name)
        
        if nc:
            await nc.close()
            logger.info("Disconnected from NATS")
        
        if config.aggregator.serialize_to:
            with open(config.aggregator.serialize_to, "w") as f:
                json.dump(aggregator.to_dict(), f, indent=4)
                logger.info(f"Serialized aggregator to {config.aggregator.serialize_to}")
        
        logger.info("Shutdown complete")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="NATS JetStream Trade Consumer")
    parser.add_argument(
        "--config", 
        default="config/osiris.json",
        help="Path to configuration file (default: config/osiris.json)"
    )
    args = parser.parse_args()
    
    logger.info("NATS JetStream Trade Consumer")
    logger.info(f"Using configuration file: {args.config}")
    logger.info("Press Ctrl+C to stop\n")
    
    try:
        asyncio.run(main(args.config))
    except KeyboardInterrupt:
        # This should not happen with our signal handling, but just in case
        logger.info("Program interrupted")
    except Exception as e:
        logger.error(f"Configuration error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Exiting...")
        sys.exit(0)