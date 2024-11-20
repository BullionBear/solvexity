from .all_in import AllIn

class PolicyFactory:
   def __init__(self, trade_context, policy_config: dict):
        self.trade_context = trade_context
        self.policy_config = policy_config

    def __getitem__(self, policy_name: str):
        return self.get_policy(policy_name)

    def get_policy(self, policy_name: str):
        if policy_name == "allin":
            return AllIn(
                self.trade_context,
                **self.policy_config["allin"]
            )
        else:
            raise ValueError(f"Unknown policy: {policy_name}")
