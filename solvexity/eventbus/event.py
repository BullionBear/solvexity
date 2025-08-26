from typing import Any
from pydantic import BaseModel, Field
import uuid
import time

class Event(BaseModel):
    time_ms: int = Field(default_factory=lambda: int(time.time() * 1000))
    uid: str = Field(default_factory=lambda: str(uuid.uuid4()))
    data: Any