from dataclasses import dataclass, field
from typing import Any
import time
from enum import Enum
import uuid

class EventType(Enum):
    BAR = "bar"

@dataclass
class Event:
    type: EventType
    data: Any
    timestamp: int = field(default_factory=lambda: int(time.time() * 1000))
    uuid: str = field(default_factory=lambda: str(uuid.uuid4()))