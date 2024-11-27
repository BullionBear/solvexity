from fastapi import Request
from trader.config import ConfigLoader


def get_config_loader(request: Request)-> ConfigLoader:
    return request.app.state.config_loader
