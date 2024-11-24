import helper
from service import ServiceFactory
from trader.data.provider import DataProviderFactory
from trader.context import ContextFactory
from trader.signal import SignalFactory
from trader.policy import PolicyFactory
from trader.strategy import StrategyFactory


class ConfigLoader:
    def __init__(self, config: dict):
        self.config = config

    def __getitem__(self, service_name: str):
        if service_name == "services":
            return self.get_service_factory()
        elif service_name == "data":
            return self.get_data_factory()
        elif service_name == "contexts":
            return self.get_context_factory()
        elif service_name == "signals":
            return self.get_signal_factory()
        elif service_name == "policies":
            return self.get_policy_factory()
        elif service_name == "strategies":
            return self.get_strategy_factory()
        else:
            raise ValueError(f"Service '{service_name}' not supported. Available services: {list(self.config.keys())}")
    
    def get_service_factory(self):
        return ServiceFactory(self.config["services"])
    
    def get_data_factory(self):
        service_factory = self.get_service_factory()
        return DataProviderFactory(service_factory, self.config["data"])
    
    def get_context_factory(self):
        service_factory = self.get_service_factory()
        return ContextFactory(service_factory, self.config["contexts"])
    
    def get_signal_factory(self):
        context_factory = self.get_context_factory()
        return SignalFactory(context_factory, self.config["signals"])
    
    def get_policy_factory(self):
        context_factory = self.get_context_factory()
        return PolicyFactory(context_factory, self.config["policies"])
    
    def get_strategy_factory(self):
        signal_factory = self.get_signal_factory()
        policy_factory = self.get_policy_factory()
        return StrategyFactory(signal_factory, policy_factory, self.config["strategies"])
    
    @classmethod
    def from_file(cls, file_path: str):
        config = helper.load_config(file_path)
        return cls(config)
    