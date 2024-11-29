import json
from .command import Command
from trader.config import ConfigLoader

class CommandHandler:
    def __init__(self, config_loader: ConfigLoader, command: Command):
        self.command = command
        self.config_loader = config_loader
    
    

    