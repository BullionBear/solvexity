from trader.context import ContextFactory
from .all_in import AllIn

# Registry for available policies
POLICY_FACTORY_REGISTRY = {
    "all_in": lambda context, config: AllIn(
        trade_context=context,
        symbol=config["symbol"],
        trade_id=config["trade_id"]
    )
}

class PolicyFactory:
    _instances = {}
    def __init__(self, context_factory: ContextFactory, policy_config: dict):
        self.context_factory = context_factory
        self.policy_config = policy_config

    def __getitem__(self, policy_name: str):
        return self.get_policy(policy_name)

    def get_policy(self, policy_name: str):
        # Check if the policy is already created
        if policy_name in self._instances:
            return self._instances[policy_name]

        # Fetch the policy configuration by name
        policy_config = self.policy_config.get(policy_name)
        if not policy_config:
            available_policies = ", ".join(self.policy_config.keys())
            raise ValueError(
                f"Policy '{policy_name}' not found in the configuration. "
                f"Available policies: {available_policies}"
            )

        # Fetch the factory name and function
        factory_name = policy_config["factory"]
        factory_function = POLICY_FACTORY_REGISTRY.get(factory_name)
        if not factory_function:
            raise ValueError(
                f"Policy factory '{factory_name}' is not registered. "
                f"Registered factories: {list(POLICY_FACTORY_REGISTRY.keys())}"
            )

        # Resolve the trade context
        context_ref = policy_config.get("trade_context")
        if not context_ref or not context_ref.startswith("contexts."):
            raise ValueError(
                f"Invalid or missing trade context reference '{context_ref}' for policy '{policy_name}'."
            )
        context_name = context_ref.split(".")[1]
        trade_context = self.context_factory.get_context(context_name)

        # Create the policy instance and cache it
        instance = factory_function(trade_context, policy_config)
        self._instances[policy_name] = instance
        return instance
