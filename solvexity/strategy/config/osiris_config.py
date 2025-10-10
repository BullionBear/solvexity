from typing import List, Optional
from pydantic import BaseModel, Field
from .config_parser import yml_to_dict
import time
from datetime import datetime

_TIMESTAMP = int(time.time())

class AggregatorConfig(BaseModel):
    type: str = "quote_volume"
    serialize_to: str = ""
    deserialize_from: str = ""
    
class ConsumerConfig(BaseModel):
    nats_url: str = "nats://localhost:4222"
    stream: str = "TRADE"
    name: str = f"TRADE_FANOUT_BTCUSDT_{_TIMESTAMP}"
    description: str = "Pub-sub consumer for trade data broadcasting"
    durable_name: str = f"TRADE_FANOUT_BTCUSDT_{_TIMESTAMP}"
    deliver_policy: str = "by_start_time"
    opt_start_time: int = 0
    ack_policy: str = "none"
    ack_wait: int = 0
    max_deliver: int = 1
    replay_policy: str = "instant"
    sample_freq: str = ""
    rate_limit_bps: int = 10000000
    max_ack_pending: int = 0
    idle_heartbeat: int = 0
    flow_control: bool = False
    deliver_subject: str = f"fanout.binance.spot.btcusdt.{_TIMESTAMP}"
    deliver_group: str = ""
    filter_subject: str = "trade.binance.spot.btcusdt"

class AlphaConfig(BaseModel):
    recv_window: int = 5000



class OsirisConfig(BaseModel):
    """Main configuration class for Osiris strategy with environment variable support."""
    aggregator: AggregatorConfig
    consumer: ConsumerConfig
    alpha: AlphaConfig

    @classmethod
    def from_yaml(cls, yaml_path: str, substitute_env: bool = True) -> "OsirisConfig":
        """
        Load configuration from YAML file with environment variable substitution.
        
        Args:
            yaml_path: Path to the YAML configuration file
            substitute_env: If True, substitute environment variables in the YAML content
            
        Returns:
            OsirisConfig instance with values loaded from YAML
            
        Example YAML:
            ```yaml
            aggregator:
              type: quote_volume
              serialize_to: ./artifacts/aggregator.json
              deserialize_from: ./artifacts/aggregator.json
            consumer:
              nats_url: nats://localhost:4222
              stream: TRADE
              rate_limit_bps: 10000000
              filter_subject: trade.binance.spot.btcusdt
            alpha:
              recv_window: 5000
            ```
        """
        config_dict = yml_to_dict(yaml_path, substitute_env=substitute_env)
        return cls(**config_dict)
    