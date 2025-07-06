"""
YAML Configuration Parser with Environment Variable Support

This module provides utilities for parsing YAML configuration files
with support for environment variable substitution using ${VAR} syntax.
"""

import os
import re
import yaml
from typing import Any, Dict, Union, Optional
from pathlib import Path


class ConfigError(Exception):
    """Custom exception for configuration parsing errors."""
    pass


class YAMLConfigParser:
    """
    YAML Configuration Parser with Environment Variable Substitution
    
    Supports parsing YAML files and replacing ${VAR} patterns with
    environment variable values.
    """
    
    # Regex pattern to match ${VAR} or ${VAR:default_value}
    ENV_VAR_PATTERN = re.compile(r'\$\{([^}:]+)(?::([^}]*))?\}')
    
    def __init__(self, strict_env_vars: bool = True):
        """
        Initialize the YAML config parser.
        
        Args:
            strict_env_vars: If True, raises error for missing env vars without defaults.
                           If False, leaves unresolved variables as-is.
        """
        self.strict_env_vars = strict_env_vars
    
    def _substitute_env_vars(self, value: Any) -> Any:
        """
        Recursively substitute environment variables in the configuration.
        
        Args:
            value: The value to process (can be dict, list, str, or other types)
            
        Returns:
            The value with environment variables substituted
        """
        if isinstance(value, dict):
            return {k: self._substitute_env_vars(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._substitute_env_vars(item) for item in value]
        elif isinstance(value, str):
            return self._substitute_string_env_vars(value)
        else:
            return value
    
    def _substitute_string_env_vars(self, text: str) -> str:
        """
        Substitute environment variables in a string.
        
        Supports patterns:
        - ${VAR} - substitute with environment variable value
        - ${VAR:default} - substitute with env var or default if not set
        
        Args:
            text: String that may contain environment variable references
            
        Returns:
            String with environment variables substituted
        """
        def replacer(match):
            var_name = match.group(1)
            default_value = match.group(2) if match.group(2) is not None else None
            
            # Get environment variable value
            env_value = os.environ.get(var_name)
            
            if env_value is not None:
                return env_value
            elif default_value is not None:
                return default_value
            elif self.strict_env_vars:
                raise ConfigError(f"Environment variable '{var_name}' not found and no default provided")
            else:
                # Return the original pattern if not strict
                return match.group(0)
        
        return self.ENV_VAR_PATTERN.sub(replacer, text)
    
    def parse_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Parse a YAML configuration file.
        
        Args:
            file_path: Path to the YAML configuration file
            
        Returns:
            Dictionary with parsed configuration and environment variables substituted
            
        Raises:
            ConfigError: If file cannot be read or parsed
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise ConfigError(f"Configuration file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                raw_config = yaml.safe_load(file)
        except yaml.YAMLError as e:
            raise ConfigError(f"Failed to parse YAML file {file_path}: {e}")
        except Exception as e:
            raise ConfigError(f"Failed to read configuration file {file_path}: {e}")
        
        if raw_config is None:
            return {}
        
        # Substitute environment variables
        try:
            return self._substitute_env_vars(raw_config)
        except ConfigError:
            raise
        except Exception as e:
            raise ConfigError(f"Failed to substitute environment variables: {e}")
    
    def parse_string(self, yaml_string: str) -> Dict[str, Any]:
        """
        Parse a YAML configuration string.
        
        Args:
            yaml_string: YAML configuration as string
            
        Returns:
            Dictionary with parsed configuration and environment variables substituted
            
        Raises:
            ConfigError: If YAML cannot be parsed
        """
        try:
            raw_config = yaml.safe_load(yaml_string)
        except yaml.YAMLError as e:
            raise ConfigError(f"Failed to parse YAML string: {e}")
        
        if raw_config is None:
            return {}
        
        # Substitute environment variables
        try:
            return self._substitute_env_vars(raw_config)
        except ConfigError:
            raise
        except Exception as e:
            raise ConfigError(f"Failed to substitute environment variables: {e}")


# Convenience functions for common use cases
def load_config(file_path: Union[str, Path], strict_env_vars: bool = True) -> Dict[str, Any]:
    """
    Load and parse a YAML configuration file.
    
    Args:
        file_path: Path to the YAML configuration file
        strict_env_vars: If True, raises error for missing env vars without defaults
        
    Returns:
        Dictionary with parsed configuration
    """
    parser = YAMLConfigParser(strict_env_vars=strict_env_vars)
    return parser.parse_file(file_path)


def load_config_string(yaml_string: str, strict_env_vars: bool = True) -> Dict[str, Any]:
    """
    Load and parse a YAML configuration string.
    
    Args:
        yaml_string: YAML configuration as string
        strict_env_vars: If True, raises error for missing env vars without defaults
        
    Returns:
        Dictionary with parsed configuration
    """
    parser = YAMLConfigParser(strict_env_vars=strict_env_vars)
    return parser.parse_string(yaml_string)


def get_nested_value(config: Dict[str, Any], key_path: str, default: Any = None) -> Any:
    """
    Get a nested value from configuration using dot notation.
    
    Args:
        config: Configuration dictionary
        key_path: Dot-separated key path (e.g., "app.database.host")
        default: Default value if key path not found
        
    Returns:
        The value at the key path or default
    """
    keys = key_path.split('.')
    current = config
    
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    
    return current
