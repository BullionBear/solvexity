from typing import List, Optional
from pydantic import BaseModel, Field
from .config_parser import yml_to_dict


class AggregatorConfig(BaseModel):
    serialize_to: str = ""
    deserialize_from: str = ""
    
class ConsumerConfig(BaseModel):
    nats_url: str = "nats://localhost:4222"
    stream: str = "TRADE"
    rate_limit_bps: int = 10000000
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
    