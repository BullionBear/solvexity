from typing import Any
import solvexity.helper.logging as logging
from solvexity.dependency import ServiceFactory
from .offline_spot_feed import OfflineSpotFeed
from .online_spot_feed import OnlineSpotFeed

logger = logging.get_logger()

def create_offline_spot_feed(services: ServiceFactory, config: dict) -> OfflineSpotFeed:
    redis_instance = services[config["redis"].split(".")[1]]
    sql_engine = services[config["sql_engine"].split(".")[1]]
    return OfflineSpotFeed(
        redis=redis_instance,
        sql_engine=sql_engine,
        start=config["start"],
        end=config["end"],
        sleep_time=config["sleep_time"]
    )


def create_online_spot_feed(services: ServiceFactory, config: dict) -> OnlineSpotFeed:
    redis_instance = services[config["redis"].split(".")[1]]
    return OnlineSpotFeed(
        redis=redis_instance
    )


# Register providers in a registry
FEED_FACTORY_REGISTRY = {
    "offline_spot": create_offline_spot_feed,
    "online_spot": create_online_spot_feed
}

class FeedFactory:
    _instances: dict[str, Any] = {}
    def __init__(self, services: ServiceFactory, feed_config: dict):
        self.feed_config = feed_config
        self.services = services

    def __getitem__(self, feed_name: str):
        return self.get_feed(feed_name)

    def get_feed(self, feed_name: str):
        logger.info(f"Getting feed '{feed_name}'")
        if feed_name in self._instances:
            logger.info(f"Feed '{feed_name}' already initialized.")
            return self._instances[feed_name]

        feed_config = self.feed_config.get(feed_name)
        if not feed_config:
            raise ValueError(f"Provider '{feed_name}' not found in the configuration.")

        factory_name = feed_config["factory"]
        factory_function = FEED_FACTORY_REGISTRY.get(factory_name)
        if not factory_function:
            raise ValueError(f"Factory '{factory_name}' not registered for provider '{feed_name}'.")
        logger.info(f"Creating feed '{feed_name}' with config '{feed_config}'")
        instance = factory_function(self.services, feed_config)
        self._instances[feed_name] = instance
        return instance