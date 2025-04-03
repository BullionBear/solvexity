from typing import List, Optional, Union, Dict, Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class IntervalType(str, Enum):
    """Valid interval types for indicators"""
    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    HOUR_1 = "1h"
    HOUR_4 = "4h"
    DAY_1 = "1d"


class IndicatorType(str, Enum):
    """Valid indicator types"""
    RETURNS = "returns"
    VOLATILITY = "volatility"
    MDD = "mdd"
    SKEWNESS = "skewness"
    KURTOSIS = "kurtosis"
    STOPPING_RETURN = "stopping_return"


class BaseIndicator(BaseModel):
    """Base model for all indicators"""
    name: str
    type: IndicatorType
    symbol: str
    interval: IntervalType
    period: int = Field(gt=0, description="Number of periods")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Ensure name follows the expected pattern"""
        if not v or not isinstance(v, str):
            raise ValueError("Name must be a non-empty string")
        return v


class LookbackIndicator(BaseIndicator):
    """Model for lookback indicators"""
    pass


class LookafterIndicator(BaseIndicator):
    """Model for lookafter indicators"""
    stop_loss: Optional[float] = None
    stop_profit: Optional[float] = None
    
    @field_validator('stop_loss', 'stop_profit')
    @classmethod
    def validate_stopping_params(cls, v, info):
        """Validate stopping parameters for stopping_return type"""
        if info.data.get('type') == IndicatorType.STOPPING_RETURN and v is None:
            raise ValueError(f"{info.data.get('type')} requires stop_loss and stop_profit values")
        return v


class IndicatorsConfig(BaseModel):
    """Model for the indicators configuration"""
    lookback: List[LookbackIndicator]
    lookafter: List[LookafterIndicator]


class PipelineConfig(BaseModel):
    """Model for pipeline configuration"""
    q: float
    path: str


class DistributionConfig(BaseModel):
    """Model for distribution configuration"""
    pipelines: List[PipelineConfig]
    x_columns: List[Union[str, Dict[str, Any]]]


class AgentConfig(BaseModel):
    """Model for agent configuration"""
    type: str
    distribution: DistributionConfig


class GrpcConfig(BaseModel):
    """Model for gRPC configuration"""
    host: str
    port: int
    timeout: int
    max_workers: int
    max_message_length: int


class RedisConfig(BaseModel):
    """Model for Redis configuration"""
    host: str
    port: int
    db: int
    password: str


class Config(BaseModel):
    """Root configuration model"""
    indicators: IndicatorsConfig
    grpc: GrpcConfig
    redis: RedisConfig
    agent: AgentConfig 