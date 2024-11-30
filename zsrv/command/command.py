import json
from .const import ALL_METHOD, ERROR

class Response:
    def __init__(self, response: ALL_METHOD, **kwargs):
        self.response = response
        self.kwargs = kwargs
        pass

class Command:
    def __init__(self, command: ALL_METHOD, **kwargs):
        self.command = command
        self.kwargs = kwargs

    @classmethod
    def from_bytes(cls, byte_data: bytes):
        try:
            json_data = json.loads(byte_data.decode('utf-8'))
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON format")
        command = json_data.get("command", '')
        if command not in ALL_METHOD.__dict__.values():
            return cls(ERROR.CMD_NOT_FOUND, message="Only valid commands are allowed")
        return cls(command, **json_data.get("kwargs", {}))
    
    