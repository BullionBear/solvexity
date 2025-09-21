from solvexity.agent.agent import Agent
from solvexity.model.enum import Exchange, Symbol

class EnterUntil(Agent):
    def __init__(self, 
                exchange: Exchange, 
                symbol: Symbol, 
                size: float, 
                max_holding_period: int, 
                stop_loss_pct: float, 
                take_profit_pct: float,
                ):
        # Configuration
        self.exchange = exchange
        self.symbol = symbol
        self.size = size
        self.max_holding_period = max_holding_period
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.position = 0

    async def enter(self):
        return True