"""
Configuration module for Solvexity strategies.

Provides YAML/JSON configuration loading with environment variable substitution support.
"""

from .osiris_config import (
    OsirisConfig
)

__all__ = [
    'OsirisConfig',
]
