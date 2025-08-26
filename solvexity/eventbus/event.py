from typing import Any
from pydantic import BaseModel


class Event(BaseModel):
    time_ms: int
    source: str
    target: str
    data: Any