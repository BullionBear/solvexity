from service import ServiceFactory
from .live_trade import LiveTradeContext
from .paper_trade import PaperTradeContext

class TradeContextFactory:
    def __init__(self, services: ServiceFactory, context_config: dict):
        self.service = services
        self.context_config = context_config

    def __getitem__(self, context_name: str):
        return self.get_context(context_name)

    def get_context(self, policy_name: str):
        if policy_name == "paper":
            return PaperTradeContext(
                
                **self.context_config["paper"]
            )
        elif policy_name == "live":
            return LiveTradeContext(
                **self.context_config["live"]
            )
        else:
            raise ValueError(f"Unknown policy: {policy_name}")