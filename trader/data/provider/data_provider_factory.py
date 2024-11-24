from service import ServiceFactory
from .historical_provider import HistoricalProvider
from .realtime_provider import RealtimeProvider


def create_historical_provider(services: ServiceFactory, config: dict) -> HistoricalProvider:
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


def create_realtime_provider(services: ServiceFactory, config: dict) -> RealtimeProvider:
    redis_instance = services[config["redis"].split(".")[1]]
    return RealtimeProvider(
        redis=redis_instance,
        symbol=config["symbol"],
        granular=config["granular"],
        limit=config["limit"]
    )


# Register providers in a registry
DATA_PROVIDER_FACTORY_REGISTRY = {
    "historical": create_historical_provider,
    "realtime": create_realtime_provider
}

class DataProviderFactory:
    _instances = {}
    def __init__(self, services: ServiceFactory, provider_config: dict):
        self.provider_config = provider_config
        self.services = services

    def __getitem__(self, provider_name: str):
        return self.get_provider(provider_name)

    def get_provider(self, provider_name: str):
        if provider_name in self._instances:
            return self._instances[provider_name]

        provider_config = self.provider_config.get(provider_name)
        if not provider_config:
            raise ValueError(f"Provider '{provider_name}' not found in the configuration.")

        factory_name = provider_config["factory"]
        factory_function = DATA_PROVIDER_FACTORY_REGISTRY.get(factory_name)
        if not factory_function:
            raise ValueError(f"Factory '{factory_name}' not registered for provider '{provider_name}'.")

        instance = factory_function(self.services, provider_config)
        self._instances[provider_name] = instance
        return instance