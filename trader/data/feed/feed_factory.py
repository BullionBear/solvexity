from dependency import ServiceFactory
from .offline_feed import HistoricalProvider
from .online_feed import RealtimeProvider


def create_offline_feed(services: ServiceFactory, config: dict) -> HistoricalProvider:
    redis_instance = services[config["redis"].split(".")[1]]
    sql_engine = services[config["sql_engine"].split(".")[1]]
    return HistoricalProvider(
        redis=redis_instance,
        sql_engine=sql_engine,
        symbol=config["symbol"],
        granular=config["granular"],
        start=config["start"],
        end=config["end"],
        limit=config["limit"],
        sleep_time=config["sleep_time"]
    )


def create_online_feed(services: ServiceFactory, config: dict) -> RealtimeProvider:
    redis_instance = services[config["redis"].split(".")[1]]
    return RealtimeProvider(
        redis=redis_instance,
        symbol=config["symbol"],
        granular=config["granular"],
        limit=config["limit"]
    )


# Register providers in a registry
FEED_FACTORY_REGISTRY = {
    "offline": create_offline_feed,
    "online": create_online_feed
}

class FeedFactory:
    _instances = {}
    def __init__(self, services: ServiceFactory, feed_config: dict):
        self.feed_config = feed_config
        self.services = services

    def __getitem__(self, feed_name: str):
        return self.get_feed(feed_name)

    def get_feed(self, feed_name: str):
        if feed_name in self._instances:
            return self._instances[feed_name]

        feed_config = self.feed_config.get(feed_name)
        if not feed_config:
            raise ValueError(f"Provider '{feed_name}' not found in the configuration.")

        factory_name = feed_config["factory"]
        factory_function = FEED_FACTORY_REGISTRY.get(factory_name)
        if not factory_function:
            raise ValueError(f"Factory '{factory_name}' not registered for provider '{feed_name}'.")

        instance = factory_function(self.services, feed_config)
        self._instances[feed_name] = instance
        return instance