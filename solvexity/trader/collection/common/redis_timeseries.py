from typing import Any, AsyncGenerator, Callable
from pydantic import BaseModel
from hooklet.base import BasePilot
from hooklet.types import HookletMessage
from solvexity.trader.base.config_node import ConfigNode
from solvexity.connector.types import OHLCV, Symbol, Trade
from solvexity.logger import SolvexityLogger
from solvexity.utils import str_to_ms

class RedisCache(ConfigNode):
    