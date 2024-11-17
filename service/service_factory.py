import redis
from sqlalchemy.engine import Engine
from binance.client import Client as BinanceClient
from .socket_argparser import SocketArgparser

def get_redis(host: str, port: int, db: int) -> redis.Redis:
    return redis.Redis(host=host, port=port, db=db)

def get_sqlengine(host: str, port: int, username: str, password: str, db: str) -> Engine:
    from sqlalchemy import create_engine
    return create_engine(f"postgresql://{username}:{password}@{host}:{port}/{db}")

def get_binance_client(api_key: str, api_secret: str) -> BinanceClient:
    return BinanceClient(api_key, api_secret)

class ServiceFactory:
    def __init__(self, services_config: dict):
        self.services_config = services_config

    def __getitem__(self, service_name: str):
        return self.get_service(service_name)

    def get_service(self, service_name: str):
        if service_name == "redis":
            return self.get_redis()
        elif service_name == "sql":
            return self.get_sqlengine()
        elif service_name == "binance":
            return self.get_binance_client()
        elif service_name == "webhook":
            return self.get_webhook()
        elif service_name == "tcp":
            return self.get_tcp()
        else:
            raise ValueError(f"Unknown service: {service_name}")

    def get_redis(self) -> redis.Redis:
        return get_redis(
            self.services_config["redis"]["host"],
            self.services_config["redis"]["port"],
            self.services_config["redis"]["db"]
        )

    def get_sqlengine(self) -> Engine:
        return get_sqlengine(
            self.services_config["sql"]["host"],
            self.services_config["sql"]["port"],
            self.services_config["sql"]["username"],
            self.services_config["sql"]["password"],
            self.services_config["sql"]["db"]
        )

    def get_binance_client(self) -> BinanceClient:
        return get_binance_client(
            self.services_config["binance"]["api_key"],
            self.services_config["binance"]["api_secret"]
       )
    
    def get_webhook(self) -> str:
        return self.services_config["webhook"]
    
    def get_tcp(self) -> SocketArgparser:
        return SocketArgparser(self.services_config["tcp"]["host"], self.services_config["tcp"]["port"])