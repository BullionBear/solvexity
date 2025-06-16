from pydantic import BaseModel
from typing import Optional

class NatsConfig(BaseModel):
    url: str = "nats://localhost:4222"

class LoggingConfig(BaseModel):
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

class ServerConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000

class AppConfig(BaseModel):
    server: ServerConfig = ServerConfig()
    nats: NatsConfig = NatsConfig()
    logging: LoggingConfig = LoggingConfig() 