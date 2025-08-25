from datetime import datetime, timedelta

from solvexity.agent.agent import Agent
from solvexity.connector.base import ExchangeConnector
from solvexity.connector.types import OrderSide, Symbol


class Hold(Agent):
    def __init__(self, hold_time_ms: int, symbol: Symbol, side: OrderSide, quantity: float, connector: ExchangeConnector):
        # Configuration
        self.hold_time_ms = hold_time_ms
        self.connector = connector
        # State
        self.hold_until = datetime.now() + timedelta(milliseconds=self.hold_time_ms)
