from solvexity.model.bar import Bar
import numpy as np
from collections import deque

class ExponentialMovingAverage:
    def __init__(self, buffer_size: int, decay: float): # decay = 0 implies simple moving average
        self.buffer_size = buffer_size
        self.decay = decay
        self.buffer = [0] * buffer_size
        self.offset = 0
        self.length = 0

    def on_bar(self, bar: Bar):
        self.buffer[self.offset] = bar.close
        self.offset = (self.offset + 1) % self.buffer_size
        self.length += 1
        if self.length > self.buffer_size:
            self.buffer.pop(0)
        return self.buffer.mean()