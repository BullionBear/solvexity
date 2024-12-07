import redis
from typing import Any
from sqlalchemy.engine import Engine
from binance.client import Client as BinanceClient
from sqlalchemy import create_engine
from .notification import Notification
from pymongo import MongoClient

# Individual factory methods for service creation
def create_redis(config: dict) -> redis.Redis:
    return redis.Redis(
        host=config["host"],
        port=config["port"],
        db=config["db"]
    )

def create_mongo_client(config: dict) -> MongoClient:
    return MongoClient(
        f"mongodb://{config['username']}:{config['password']}@{config['host']}:{config['port']}/{config['db']}?authSource=admin"
    )

def create_sql_engine(config: dict) -> Engine:
    return create_engine(
        f"postgresql://{config['username']}:{config['password']}@{config['host']}:{config['port']}/{config['db']}"
    )

def create_binance_client(config: dict) -> BinanceClient:
    return BinanceClient(config["api_key"], config["api_secret"])


def create_notification(config: dict) -> Notification:
    return Notification(config["webhook"], config["enabled"])



# A registry of factory methods for dynamic service creation
FACTORY_REGISTRY = {
    "redis": create_redis,
    "sqlengine": create_sql_engine,
    "binance": create_binance_client,
    "notify": create_notification,
    "mongo": create_mongo_client
}


# Refactored ServiceFactory
class ServiceFactory:
    _instances: dict[str, Any] = {}
    def __init__(self, services_config: dict):
        self.services_config = services_config

    def __getitem__(self, service_name: str):
        return self.get_service(service_name)

    def get_service(self, service_name: str):
        if service_name in self._instances:
            return self._instances[service_name]

        service_config = self.services_config.get(service_name)
        if not service_config:
            raise ValueError(f"Dependency '{service_name}' not found in the configuration.")

        # Extract the factory and specific config
        factory_name = service_config["factory"]
        factory_config = {k: v for k, v in service_config.items() if k != "factory"}

        # Dynamically resolve and create the service
        factory_function = FACTORY_REGISTRY.get(factory_name)
        if not factory_function:
            raise ValueError(f"Factory '{factory_name}' not registered for service '{service_name}'.")

        instance = factory_function(factory_config)
        self._instances[service_name] = instance
        return instance
