import solvexity.helper.logging as logging
from solvexity.trader.context import ContextFactory
from .all_in_spot_policy import AllInSpotPolicy
from .fix_quote_spot_policy import FixQuoteSpotPolicy
from .fix_base_perp_policy import FixBasePerpPolicy

logger = logging.getLogger()

# Registry for available policies
POLICY_FACTORY_REGISTRY = {
    "all_in_spot_policy": lambda context, config: AllInSpotPolicy(
        trade_context=context,
        symbol=config["symbol"],
        trade_id=config["trade_id"]
    ),
    "fix_quote_spot_policy": lambda context, config: FixQuoteSpotPolicy(
        trade_context=context,
        symbol=config["symbol"],
        quote_size=config["quote_size"],
        trade_id=config["trade_id"]
    ),
    "fix_base_perp_policy": lambda context, config: FixBasePerpPolicy(
        trade_context=context,
        symbol=config["symbol"],
        base_size=config["base_size"],
        is_reversed=config["is_reversed"],
        trade_id=config["trade_id"]
    )
}

class PolicyFactory:
    _instances = {}
    def __init__(self, context_factory: ContextFactory, policy_config: dict):
        self.context_factory = context_factory
        self.policy_config = policy_config
        self._instances = {}

    def __getitem__(self, policy_name: str):
        return self.get_policy(policy_name)

    def get_policy(self, policy_name: str):
        logger.info(f"Getting policy '{policy_name}'")
        # Check if the policy is already created
        if policy_name in self._instances:
            logger.info(f"Policy '{policy_name}' already initialized.")
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
        logger.info(f"Creating policy '{policy_name}' with config '{policy_config}'")
        # Create the policy instance and cache it
        instance = factory_function(trade_context, policy_config)
        self._instances[policy_name] = instance
        return instance
