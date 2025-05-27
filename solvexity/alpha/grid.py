import numpy as np
from typing import List, Dict, Any, Tuple
from collections import defaultdict
import bisect

class Grid:
    def __init__(self, price_low: float, price_high: float, grid_size: int, timescale: int):
        self._price_grid = np.logspace(price_low, price_high, num=grid_size)
        self._timescale = timescale
        self._grid: Dict[Tuple[int, int], Dict[str, float]] = defaultdict(dict)

    
    def _add(self, price: float, timestamp: int, key: str, value: float) -> None:
        px_idx = bisect.bisect_left(self._price_grid, price)
        ts_idx = timestamp // self._timescale
        if px_idx < len(self._price_grid) and ts_idx >= 0:
            self._grid[(px_idx, ts_idx)][key] = value
        else:
            raise ValueError("Price or timestamp index out of bounds.")
    
    