"""
Simple logger module for solvexity
"""

import logging
from typing import Optional


class SolvexityLogger:
    """Simple logger class for solvexity"""
    
    def __init__(self):
        self._logger = None
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger instance"""
        if self._logger is None:
            # Set up basic logging if not already configured
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            self._logger = logging.getLogger(name)
        return self._logger


class SolvexityLoggerConfig:
    """Logger configuration class"""
    
    def __init__(self, level: str = "INFO", format: str = None):
        self.level = level
        self.format = format or '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
