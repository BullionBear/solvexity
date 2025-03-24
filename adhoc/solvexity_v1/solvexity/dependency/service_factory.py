import redis
from typing import Any
from sqlalchemy.engine import Engine
from binance.client import Client as BinanceClient
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from .notification import Notification
from pymongo import MongoClient
import solvexity.helper.logging as logging

logger = logging.getLogger()

# Individual factory methods for service creation
def create_redis(config: dict) -> redis.Redis:
    try:
        # Create Redis instance
        r = redis.Redis(
            host=config["host"],
            port=config["port"],
            db=config["db"],
            **config.get("options", {})  # Allow optional parameters
        )
        # Test the connection
        r.ping()
        logger.info("Connected to Redis successfully.")
        return r
    except redis.ConnectionError as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise
    

def create_mongo_client(config: dict) -> MongoClient:
    try:
        # Create MongoDB client
        client = MongoClient(
            f"mongodb://{config['username']}:{config['password']}@{config['host']}:{config['port']}/{config['db']}?authSource=admin"
        )
        # Test the connection
        client.admin.command('ping')
        logger.info("Connected to MongoDB successfully.")
        return client
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise

def create_sql_engine(config: dict) -> Engine:
    try:
        # Create SQLAlchemy engine
        engine = create_engine(
            f"postgresql://{config['username']}:{config['password']}@{config['host']}:{config['port']}/{config['db']}"
        )
        # Test the connection
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            logger.info(f"connection successful: {result.scalar() == 1}")
        return engine
    except OperationalError as e:
        logger.error(f"Failed to connect to PostgreSQL: {e}")
        raise

def create_binance_client(config: dict) -> BinanceClient:
    try:
        # Create Binance client
        client = BinanceClient(config["api_key"], config["api_secret"])
        # Test the connection
        client.ping()
        logger.info("Connected to Binance successfully.")
        return client
    except Exception as e:
        logger.error(f"Failed to connect to Binance: {e}")
        raise


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
        logger.info(f"Creating service {service_name} with config {factory_config}")
        instance = factory_function(factory_config)
        self._instances[service_name] = instance
        return instance
