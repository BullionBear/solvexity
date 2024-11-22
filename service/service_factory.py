import redis
from sqlalchemy.engine import Engine
from binance.client import Client as BinanceClient
from .socket_argparser import SocketArgparser
from .notification import Notification
from sqlalchemy import create_engine


# Individual factory methods for creating services
def create_redis(host: str, port: int, db: int) -> redis.Redis:
    return redis.Redis(host=host, port=port, db=db)


def create_sql_engine(host: str, port: int, username: str, password: str, db: str) -> Engine:
    return create_engine(f"postgresql://{username}:{password}@{host}:{port}/{db}")


def create_binance_client(api_key: str, api_secret: str) -> BinanceClient:
    return BinanceClient(api_key, api_secret)


def create_notification(webhook: str) -> Notification:
    return Notification(webhook)


def create_tcp_socket(host: str, port: int) -> SocketArgparser:
    return SocketArgparser(host, port)


# ServiceFactory for managing services
class ServiceFactory:
    def __init__(self, services_config: dict):
        self.services_config = services_config
        self._service_creators = {
            "redis": self._create_redis,
            "sqlengine": self._create_sql_engine,
            "binance": self._create_binance_client,
            "notify": self._create_notification,
            "tcp": self._create_tcp_socket,
        }

    def __getitem__(self, service_name: str):
        return self.get_service(service_name)

    def get_service(self, service_name: str):
        creator = self._service_creators.get(service_name)
        if not creator:
            raise ValueError(f"Unknown service: {service_name}")
        return creator()

    # Internal methods for each service
    def _create_redis(self) -> redis.Redis:
        redis_config = self.services_config["redis"]
        return create_redis(
            host=redis_config["host"],
            port=redis_config["port"],
            db=redis_config["db"]
        )

    def _create_sql_engine(self) -> Engine:
        sql_config = self.services_config["sql"]
        return create_sql_engine(
            host=sql_config["host"],
            port=sql_config["port"],
            username=sql_config["username"],
            password=sql_config["password"],
            db=sql_config["db"]
        )

    def _create_binance_client(self) -> BinanceClient:
        binance_config = self.services_config["binance"]
        return create_binance_client(
            api_key=binance_config["api_key"],
            api_secret=binance_config["api_secret"]
        )

    def _create_notification(self) -> Notification:
        notify_config = self.services_config["notify"]
        return create_notification(webhook=notify_config["webhook"])

    def _create_tcp_socket(self) -> SocketArgparser:
        tcp_config = self.services_config["tcp"]
        return create_tcp_socket(
            host=tcp_config["host"],
            port=tcp_config["port"]
        )
