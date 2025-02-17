from abc import ABC, abstractmethod
import json
from typing import Type, TypeVar
from .const import ERROR

# Define a generic type variable for Commands
C = TypeVar('C', bound='Command')

class CommandHandler(ABC):
    @abstractmethod
    def execute(self, cmd: 'Command') -> 'Command':
        """
        Abstract method to execute a command.
        Must be implemented by subclasses.
        """
        pass

class Command:
    def __init__(self, command: str, **kwargs):
        self.command: str = command
        self.kwargs: dict = kwargs

    def execute(self: C, handler: CommandHandler) -> C:
        """
        Executes the command with the given handler.
        Returns the command instance (or subclass instance).
        """
        if self.command in ERROR.__dict__.values():
            return self
        return handler.execute(self)
    
    @classmethod
    def from_string(cls: Type[C], str_data: str) -> C:
        """
        Creates a Command instance from a JSON string.
        """
        try:
            json_data = json.loads(str_data)
        except json.JSONDecodeError:
            return cls(ERROR.CMD_JSON_DECODE_ERROR, message="Invalid JSON format")
        command = json_data.get("command", '')
        return cls(command, **json_data.get("kwargs", {}))
    
    @classmethod
    def from_dict(cls: Type[C], data: dict) -> C:
        """
        Creates a Command instance from a JSON dictionary.
        """
        command = data.get("command", '')
        return cls(command, **data.get("kwargs", {}))
    
    def to_dict(self) -> dict:
        """
        Converts the Command instance to a JSON string.
        """
        return {"command": self.command, "data": self.kwargs}
