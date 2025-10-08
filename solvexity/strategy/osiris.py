import asyncio
import json
import logging
import signal
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional
import nats
from nats.aio.msg import Msg
from nats.js.api import ConsumerConfig, DeliverPolicy, AckPolicy, ReplayPolicy

from solvexity.logging import setup_logging
from solvexity.model.trade import Trade
import solvexity.strategy as strategy
from solvexity.toolbox.aggregator import (
    TimeBarAggregator, TickBarAggregator, BaseVolumeBarAggregator, QuoteVolumeBarAggregator
)
from solvexity.eventbus import EventBus
from solvexity.eventbus.event import Event



setup_logging()

logger = logging.getLogger(__name__)

# Global shutdown event
shutdown_event = asyncio.Event()


class ConfigError(Exception):
    """Custom exception for configuration parsing errors."""
    pass


class JetStreamConsumerConfig:
    """Configuration for JetStream consumer."""
    
    def __init__(self, config: Dict[str, Any]):
        self.name = config.get("name")
        self.description = config.get("description")
        self.durable_name = config.get("durable_name")
        self.deliver_policy = config.get("deliver_policy", "all")
        self.ack_policy = config.get("ack_policy", "none")
        self.ack_wait = config.get("ack_wait", 0)
        self.max_deliver = config.get("max_deliver", 1)
        self.filter_subject = config.get("filter_subject")
        self.replay_policy = config.get("replay_policy", "instant")
        self.sample_freq = config.get("sample_freq", "")
        self.rate_limit_bps = config.get("rate_limit_bps", 10000000)
        self.max_ack_pending = config.get("max_ack_pending", 0)
        self.idle_heartbeat = config.get("idle_heartbeat", 0)
        self.flow_control = config.get("flow_control", False)
        self.deliver_subject = config.get("deliver_subject")
        self.deliver_group = config.get("deliver_group", "")
        
        # Validate required fields
        if not self.name:
            raise ConfigError("Consumer name is required")
        if not self.filter_subject:
            raise ConfigError("Consumer filter_subject is required")
        if not self.deliver_subject:
            raise ConfigError("Consumer deliver_subject is required")


class AggregatorConfig:
    """Configuration for bar aggregator."""
    
    def __init__(self, config: Dict[str, Any]):
        self.type = config.get("type", "quote_volume")
        self.buf_size = config.get("buf_size", 300)
        self.reference_cutoff = config.get("reference_cutoff", 200000)
        self.completeness_threshold = config.get("completeness_threshold", 1.0)
        
        # Deserialize
        self.deserialize_from = config.get("deserialize_from", "")
        self.serialize_to = config.get("serialize_to", "")
        
        # Validate required fields
        if self.buf_size <= 0:
            raise ConfigError("Aggregator buf_size must be positive")
        if self.reference_cutoff <= 0:
            raise ConfigError("Aggregator reference_cutoff must be positive")


class OsirisConfig:
    """Main configuration class for Osiris strategy."""
    
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self._load_config()
    
    def _load_config(self):
        """Load and validate configuration from JSON file."""
        if not self.config_path.exists():
            raise ConfigError(f"Configuration file not found: {self.config_path}")
        
        try:
            with open(self.config_path, 'r') as f:
                raw_config = json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigError(f"Failed to parse JSON file {self.config_path}: {e}")
        except Exception as e:
            raise ConfigError(f"Failed to read configuration file {self.config_path}: {e}")
        
        # Extract configuration sections
        self.stream = raw_config.get("stream", "TRADE")
        self.consumer = JetStreamConsumerConfig(raw_config.get("consumer", {}))
        self.aggregator = AggregatorConfig(raw_config.get("aggregator", {}))
        
        # Additional configuration
        self.nats_servers = raw_config.get("nats_servers", ["nats://localhost:4222"])
        self.recv_window = raw_config.get("recv_window", 5000)
        # Deserialize
        self.deserialize_from = raw_config.get("deserialize_from", "")
        self.serialize_to = raw_config.get("serialize_to", "")
        
        # Validate stream name
        if not self.stream:
            raise ConfigError("Stream name is required")


def load_config(config_path: str) -> OsirisConfig:
    """Load and validate Osiris configuration."""
    return OsirisConfig(config_path)


def get_aggregator(config: AggregatorConfig):
    """Create and return the appropriate aggregator based on configuration."""
    if config.type == "quote_volume":
        if config.deserialize_from:
            with open(config.deserialize_from, "r") as f:
                data = json.load(f)
            return QuoteVolumeBarAggregator.from_dict(data)
        else:
            return QuoteVolumeBarAggregator(
                buf_size=config.buf_size,
                reference_cutoff=config.reference_cutoff,
                completeness_threshold=config.completeness_threshold
            )
    elif config.type == "base_volume":
        if config.deserialize_from:
            with open(config.deserialize_from, "r") as f:
                data = json.load(f)
            return BaseVolumeBarAggregator.from_dict(data)
        else:
            return BaseVolumeBarAggregator(
                buf_size=config.buf_size,
                reference_cutoff=config.reference_cutoff
            )
    elif config.type == "tick":
        if config.deserialize_from:
            with open(config.deserialize_from, "r") as f:
                data = json.load(f)
            return TickBarAggregator.from_dict(data)
        else:
            return TickBarAggregator(
                buf_size=config.buf_size,
                reference_cutoff=config.reference_cutoff
            )
    elif config.type == "time":
        if config.deserialize_from:
            with open(config.deserialize_from, "r") as f:
                data = json.load(f)
            return TimeBarAggregator.from_dict(data)
        else:
            return TimeBarAggregator(
                buf_size=config.buf_size,
                reference_cutoff=config.reference_cutoff
            )
    else:
        raise ConfigError(f"Unknown aggregator type: {config.type}")

def signal_handler(sig, frame):
    """Handle shutdown signals gracefully"""
    logger.info(f"Received signal {sig}, initiating graceful shutdown...")
    shutdown_event.set()


async def setup_jetstream_consumer(js, config: OsirisConfig):
    """Set up JetStream consumer for trade data"""
    try:
        # Map string values to NATS enums
        deliver_policy_map = {
            "all": DeliverPolicy.ALL,
            "last": DeliverPolicy.LAST,
            "new": DeliverPolicy.NEW,
            "by_start_sequence": DeliverPolicy.BY_START_SEQUENCE,
            "by_start_time": DeliverPolicy.BY_START_TIME
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
        
        # Create consumer configuration
        consumer_config = ConsumerConfig(
            name=config.consumer.name,
            description=config.consumer.description,
            durable_name=config.consumer.durable_name,
            deliver_policy=deliver_policy_map.get(config.consumer.deliver_policy, DeliverPolicy.ALL),
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
        
        # Create or update the consumer
        consumer_info = await js.add_consumer(
            stream=config.stream,
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
    try:
        config = load_config(config_path)
        logger.info(f"Loaded configuration from: {config_path}")
    except ConfigError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    nc = None
    js = None
    consumer_created = False
    eb = EventBus()
    aggregator = get_aggregator(config.aggregator)
    bar_id = 0
    async def on_trade(e: Event):
        aggregator.on_trade(e.data)
        nonlocal bar_id
        if aggregator.size() != aggregator.buf_size:
            return
        if bar := aggregator.last(is_closed=True):
            if bar_id == 0:
                logger.info(f"First bar: {bar}")
                bar_id = id(bar)
            elif bar_id != id(bar):
                logger.info(f"New bar: {bar}")
                bar_id = id(bar)
            else: # same bar
                return
            if bar.close_time < int(time.time() * 1000) - config.recv_window:
                logger.info(f"Close time {bar.close_time} is less than {int(time.time() * 1000) - config.recv_window}")
                return
            df = aggregator.to_dataframe(is_closed=True)
            await eb.publish("on_dataframe", Event(data=df))

    eb.subscribe("on_trade", on_trade)

    async def on_dataframe(e: Event):
        df = e.data
        logger.info(f"Dataframe: {df.shape}")
        ref = df.iloc[-1]["close_time"]
        output_path = Path(config.output_dir) / f"dataframe_{ref}.csv"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)

    eb.subscribe("on_dataframe", on_dataframe)
    
    try:
        logger.info(f"Attempting to connect to NATS servers: {config.nats_servers}")
        # Connect to NATS
        nc = await nats.connect(servers=config.nats_servers)
        logger.info("Connected to NATS")
        
        # Get JetStream context
        js = nc.jetstream()
        logger.info("JetStream context created")
        
        # Set up JetStream consumer
        await setup_jetstream_consumer(js, config)
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
            await cleanup_consumer(js, config.stream, config.consumer.name)
        
        if nc:
            await nc.close()
            logger.info("Disconnected from NATS")
        
        if config.aggregator.serialize_to:
            with open(config.aggregator.serialize_to, "w") as f:
                json.dump(aggregator.to_dict(), f)
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
    except ConfigError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    finally:
        logger.info("Exiting...")
        sys.exit(0)