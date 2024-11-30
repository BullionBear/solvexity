import json
from .command import Command
from trader.config import ConfigLoader

class CommandHandler:
    def __init__(self, config_loader: ConfigLoader):
        self.config_loader = config_loader

    def invoke(self, command: Command) -> Command:
        pass

    
    

    