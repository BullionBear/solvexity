from abc import ABC, abstractmethod
from typing import Type, TypeVar, Protocol

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
        self.command = command
        self.kwargs = kwargs

    def execute(self: C, handler: CommandHandler) -> C:
        """
        Executes the command with the given handler.
        Returns the command instance (or subclass instance).
        """
        return handler.execute(self)
