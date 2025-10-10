"""
Configuration module for Solvexity strategies.

Provides YAML/JSON configuration loading with environment variable substitution support.
"""

from .config_parser import yml_to_dict
from .osiris_config import (
    OsirisConfig,
    ConsumerConfig,
    AggregatorConfig,
    AlphaConfig,
)

__all__ = [
    'yml_to_dict',
    'OsirisConfig',
    'ConsumerConfig',
    'AggregatorConfig',
    'AlphaConfig',
]
