import helper
import pymongo
from dependency import ServiceFactory
from trader.data.feed import FeedFactory
from trader.context import ContextFactory
from trader.signal import SignalFactory
from trader.policy import PolicyFactory
from trader.strategy import StrategyFactory


class ConfigLoader:
    def __init__(self, config: dict):
        self.config = config

    def __getitem__(self, service_name: str):
        if service_name == "dependencies":
            return self.get_service_factory()
        elif service_name == "feeds":
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
        return ServiceFactory(self.config["dependencies"])
    
    def get_data_factory(self):
        service_factory = self.get_service_factory()
        return FeedFactory(service_factory, self.config["feeds"])
    
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
    
    def get_config(self):
        return self.config 
    
    @classmethod
    def from_file(cls, file_path: str):
        config = helper.load_config(file_path)
        return cls(config)
    
    @classmethod
    def from_db(cls, mongo_client: pymongo.MongoClient, name: str):
        db = mongo_client.get_database("solvexity")
        collection = db['system']
        config = collection.find_one({"name": name})
        return cls(config)
    