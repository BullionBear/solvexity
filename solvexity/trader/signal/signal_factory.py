import solvexity.helper.logging as logging
from solvexity.trader.context import ContextFactory
from .doubly_moving_average import DoublyMovingAverage

logger = logging.getLogger("config")

def create_doubly_moving_average_signal(trade_context, config):
    return DoublyMovingAverage(
        trade_context=trade_context,
        symbol=config["symbol"],
        fast_period=config["fast_period"],
        slow_period=config["slow_period"],
        limit=config["limit"]
    )

SIGNAL_FACTORY_REGISTRY = {
    "doubly_moving_average": create_doubly_moving_average_signal,
}

class SignalFactory:
    _instances = {}
    def __init__(self, context_factory: ContextFactory, signal_config: dict):
        self.context_factory = context_factory
        self.signal_config = signal_config

    def __getitem__(self, signal_name: str):
        return self.get_signal(signal_name)

    def get_signal(self, signal_name: str):
        logger.info(f"Getting signal '{signal_name}'")
        if signal_name in self._instances:
            return self._instances[signal_name]

        signal_config = self.signal_config.get(signal_name)
        if not signal_config:
            raise ValueError(f"Signal '{signal_name}' not found in the configuration.")

        factory_name = signal_config["factory"]
        factory_function = SIGNAL_FACTORY_REGISTRY.get(factory_name)
        if not factory_function:
            raise ValueError(f"Factory '{factory_name}' not registered for signal '{signal_name}'.")

        # Resolve trade_context from the configuration
        context_ref = signal_config.get("trade_context")
        if not context_ref or not context_ref.startswith("contexts."):
            raise ValueError(
                f"Invalid or missing trade context reference '{context_ref}' for signal '{signal_name}'."
            )
        context_name = context_ref.split(".")[1]
        trade_context = self.context_factory.get_context(context_name)
        logger.info(f"Creating signal '{signal_name}' with config '{signal_config}'")
        # Create and store the signal instance
        instance = factory_function(trade_context, signal_config)
        self._instances[signal_name] = instance
        return instance
