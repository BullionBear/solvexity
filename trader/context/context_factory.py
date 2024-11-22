from service import ServiceFactory
from .live_trade import LiveTradeContext
from .paper_trade import PaperTradeContext

def create_live_trade_context(config: dict, services: dict) -> LiveTradeContext:
    # Resolve services
    binance_client = services[config["binance_client"].split(".")[1]]
    redis_instance = services[config["redis"].split(".")[1]]
    notification_service = services[config["notification"].split(".")[1]]

    # Create and return the context
    return LiveTradeContext(
        client=binance_client,
        redis=redis_instance,
        notification=notification_service,
        granular=config["granular"]
    )

def create_paper_trade_context(config: dict, services: dict) -> PaperTradeContext:
    # Resolve services
    redis_instance = services[config["redis"].split(".")[1]]

    # Create and return the context
    return PaperTradeContext(
        redis=redis_instance,
        init_balance=config["init_balance"],
        granular=config["granular"]
    )

# Register factories
CONTEXT_FACTORY_REGISTRY = {
    "live_trade": create_live_trade_context,
    "paper_trade": create_paper_trade_context
}

class ContextFactory:
    def __init__(self, services: ServiceFactory, contexts_config: dict):
        self.contexts_config = contexts_config
        self.services = services
        self._instances = {}

    def __getitem__(self, context_name: str):
        return self.get_context(context_name)

    def get_context(self, context_name: str):
        if context_name in self._instances:
            return self._instances[context_name]

        context_config = self.contexts_config.get(context_name)
        if not context_config:
            raise ValueError(f"Context '{context_name}' not found in the configuration.")

        # Get the factory and initialize the context
        factory_name = context_config["factory"]
        factory_function = CONTEXT_FACTORY_REGISTRY.get(factory_name)
        if not factory_function:
            raise ValueError(f"Factory '{factory_name}' not registered for context '{context_name}'.")

        instance = factory_function(context_config, self.services)
        self._instances[context_name] = instance
        return instance