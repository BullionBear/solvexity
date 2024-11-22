from trader.core import TradeContext
from .doubly_moving_average import DoublyMovingAverage

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
    def __init__(self, trade_context: TradeContext, signal_config: dict):
        self.trade_context = trade_context
        self.signal_config = signal_config
        self._instances = {}

    def __getitem__(self, signal_name: str):
        return self.get_signal(signal_name)

    def get_signal(self, signal_name: str):
        if signal_name in self._instances:
            return self._instances[signal_name]

        signal_config = self.signal_config.get(signal_name)
        if not signal_config:
            raise ValueError(f"Signal '{signal_name}' not found in the configuration.")

        factory_name = signal_config["factory"]
        factory_function = SIGNAL_FACTORY_REGISTRY.get(factory_name)
        if not factory_function:
            raise ValueError(f"Factory '{factory_name}' not registered for signal '{signal_name}'.")

        instance = factory_function(self.trade_context, signal_config)
        self._instances[signal_name] = instance
        return instance