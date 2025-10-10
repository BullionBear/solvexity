import os
import re
import yaml
from typing import Any, Dict


def _substitute_env_vars(value: str) -> str:
    """
    Substitute environment variables in a string.
    
    Supports the following formats:
    - ${VAR} - simple substitution
    - ${VAR:-default} - use default if VAR is unset or empty
    - ${VAR-default} - use default if VAR is unset (but not if empty)
    - ${VAR:?error_msg} - raise error if VAR is unset or empty
    - $VAR - simple format (word characters only)
    
    Args:
        value: String potentially containing environment variable references
        
    Returns:
        String with environment variables substituted
        
    Raises:
        ValueError: If a required variable (using :?) is not set
    """
    def replace_var(match: re.Match) -> str:
        # Extract the full match and variable name
        full_match = match.group(0)
        var_name = match.group(1) or match.group(2)
        
        # Handle ${VAR:?error_msg} - required variable with error message
        if match.group(1) and ':?' in full_match:
            var_base = var_name.split(':?')[0]
            error_msg = full_match.split(':?')[1].rstrip('}')
            env_value = os.environ.get(var_base)
            if not env_value:
                raise ValueError(f"Required environment variable '{var_base}' is not set: {error_msg}")
            return env_value
        
        # Handle ${VAR:-default} - default if unset or empty
        if match.group(1) and ':-' in full_match:
            var_base = var_name.split(':-')[0]
            default_value = full_match.split(':-')[1].rstrip('}')
            env_value = os.environ.get(var_base)
            return env_value if env_value else default_value
        
        # Handle ${VAR-default} - default if unset (but not if empty string)
        if match.group(1) and '-' in var_name and ':-' not in full_match:
            var_base = var_name.split('-')[0]
            default_value = full_match.split('-', 1)[1].rstrip('}')
            return os.environ.get(var_base, default_value)
        
        # Simple substitution ${VAR} or $VAR
        env_value = os.environ.get(var_name, '')
        return env_value
    
    # Pattern matches:
    # 1. ${VAR} or ${VAR:-default} or ${VAR:?error}
    # 2. $VAR (simple word characters)
    pattern = r'\$\{([^}]+)\}|\$([A-Za-z_][A-Za-z0-9_]*)'
    
    return re.sub(pattern, replace_var, value)


def _process_value(value: Any) -> Any:
    """
    Recursively process a value to substitute environment variables.
    
    Args:
        value: Value to process (can be str, dict, list, or other types)
        
    Returns:
        Processed value with environment variables substituted
    """
    if isinstance(value, str):
        return _substitute_env_vars(value)
    elif isinstance(value, dict):
        return {k: _process_value(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_process_value(item) for item in value]
    else:
        return value


def yml_to_dict(yml_path: str, substitute_env: bool = True) -> Dict[str, Any]:
    """
    Load a YAML file and optionally substitute environment variables.
    
    Args:
        yml_path: Path to the YAML file
        substitute_env: If True, substitute environment variables in the YAML content
        
    Returns:
        Dictionary representation of the YAML file with environment variables substituted
        
    Example YAML with environment variables:
        ```yaml
        database:
          host: ${DB_HOST:-localhost}
          port: ${DB_PORT:-5432}
          username: ${DB_USER:?Database user must be set}
          password: $DB_PASS
        ```
    """
    with open(yml_path, 'r') as file:
        data = yaml.safe_load(file)
    
    if substitute_env and data is not None:
        data = _process_value(data)
    
    return data