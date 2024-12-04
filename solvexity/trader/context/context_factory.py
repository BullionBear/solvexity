import solvexity.helper.logging as logging
from solvexity.trader.feed import FeedFactory
from solvexity.dependency import ServiceFactory
from .spot_trade import SpotTradeContext
from .paper_trade import PaperTradeSpotContext

logger = logging.getLogger("config")

def create_spot_trade_context(config: dict, services: ServiceFactory, feed_factory: FeedFactory) -> SpotTradeContext:
    # Resolve services
    binance_client = services[config["binance_client"].split(".")[1]]
    # redis_instance = services[config["redis"].split(".")[1]]
    notification_instance = services[config["notification"].split(".")[1]]
    feed_instance = feed_factory[config["feed"].split(".")[1]]
    # Create and return the context
    return SpotTradeContext(
        client=binance_client,
        feed=feed_instance,
        notification=notification_instance,
        granular=config["granular"]
    )

def create_spot_paper_trade_context(config: dict, services: ServiceFactory, feed_factory: FeedFactory) -> PaperTradeSpotContext:
    # Resolve services
    feed = feed_factory[config["feed"].split(".")[1]]
    notification_instance = services[config["notification"].split(".")[1]]
    # Create and return the context
    return PaperTradeSpotContext(
        feed=feed,
        notification=notification_instance,
        init_balance=config["init_balance"],
        granular=config["granular"]
    )

# Register factories
CONTEXT_FACTORY_REGISTRY = {
    "spot_trade": create_spot_trade_context,
    "spot_paper_trade": create_spot_paper_trade_context
}

class ContextFactory:
    _instances = {}
    def __init__(self, services: ServiceFactory, feeds: FeedFactory, contexts_config: dict):
        self.contexts_config = contexts_config
        self.services = services 
        self.feeds = feeds

    def __getitem__(self, context_name: str):
        return self.get_context(context_name)

    def get_context(self, context_name: str):
        logger.info(f"Getting context '{context_name}'")
        if context_name in self._instances:
            logger.info(f"Context '{context_name}' already initialized.")
            return self._instances[context_name]

        context_config = self.contexts_config.get(context_name)
        if not context_config:
            raise ValueError(f"Context '{context_name}' not found in the configuration.")

        # Get the factory and initialize the context
        factory_name = context_config["factory"]
        factory_function = CONTEXT_FACTORY_REGISTRY.get(factory_name)
        if not factory_function:
            raise ValueError(f"Factory '{factory_name}' not registered for context '{context_name}'.")
        logger.info(f"Initializing context '{context_name}' with config '{context_config}'")
        instance = factory_function(context_config, self.services, self.feeds)
        self._instances[context_name] = instance
        return instance