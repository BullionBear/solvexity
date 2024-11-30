from solvexity.trader.signal.signal_factory import SignalFactory
from solvexity.trader.policy.policy_factory import PolicyFactory
from .pythagoras import Pythagoras

# Registry for available strategy types
STRATEGY_FACTORY_REGISTRY = {
    "pythagoras": lambda signal, policy, config: Pythagoras(
        signal=signal,
        policy=policy,
        symbol=config["symbol"],
        trade_id=config["trade_id"],
        verbose=config["verbose"],
    )
}

class StrategyFactory:
    _instances = {}
    def __init__(self, signal_factory: SignalFactory, policy_factory: PolicyFactory, strategy_config: dict):
        self.signal_factory = signal_factory
        self.policy_factory = policy_factory
        self.strategy_config = strategy_config

    def __getitem__(self, strategy_name: str):
        return self.get_strategy(strategy_name)

    def get_strategy(self, strategy_name: str):
        # Check if the strategy is already created
        if strategy_name in self._instances:
            return self._instances[strategy_name]

        # Fetch the strategy configuration
        strategy_config = self.strategy_config.get(strategy_name)
        if not strategy_config:
            available_strategies = ", ".join(self.strategy_config.keys())
            raise ValueError(
                f"Strategy '{strategy_name}' not found in the configuration. "
                f"Available strategies: {available_strategies}"
            )

        # Fetch the factory name and function
        factory_name = strategy_config["factory"]
        factory_function = STRATEGY_FACTORY_REGISTRY.get(factory_name)
        if not factory_function:
            raise ValueError(
                f"Strategy factory '{factory_name}' is not registered. "
                f"Registered factories: {list(STRATEGY_FACTORY_REGISTRY.keys())}"
            )

        # Resolve signal and policy from configuration
        signal_ref = strategy_config["signal"]
        signal_name = signal_ref.split(".")[1]
        policy_ref = strategy_config["policy"]
        policy_name = policy_ref.split(".")[1]

        signal = self.signal_factory[signal_name]
        policy = self.policy_factory[policy_name]

        # Create the strategy instance and cache it
        instance = factory_function(signal, policy, strategy_config)
        self._instances[strategy_name] = instance
        return instance