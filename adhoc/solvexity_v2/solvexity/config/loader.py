import yaml
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from .models import Config, BaseIndicator


def load_config(config_path: str) -> Config:
    """
    Load and validate configuration from a YAML file.
    
    Args:
        config_path: Path to the YAML configuration file
        
    Returns:
        Validated Config object
        
    Raises:
        FileNotFoundError: If the config file doesn't exist
        ValueError: If the config file is invalid
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    try:
        with open(path, 'r') as f:
            raw_config = yaml.safe_load(f)
        
        # Process x_columns if they are dictionaries
        if 'agent' in raw_config and 'distribution' in raw_config['agent']:
            x_columns = raw_config['agent']['distribution'].get('x_columns', [])
            processed_x_columns = []
            
            for column in x_columns:
                if isinstance(column, dict):
                    # If it's already a dictionary, keep it as is
                    processed_x_columns.append(column)
                else:
                    # If it's a string, try to find the corresponding indicator
                    indicator = get_indicator_by_name_from_raw(raw_config, column)
                    if indicator:
                        processed_x_columns.append(indicator)
                    else:
                        # If not found, keep the string as is
                        processed_x_columns.append(column)
            
            raw_config['agent']['distribution']['x_columns'] = processed_x_columns
        
        # Validate against our Pydantic models
        config = Config.parse_obj(raw_config)
        return config
    except Exception as e:
        raise ValueError(f"Error loading configuration: {str(e)}")


def get_indicator_by_name(config: Config, name: str) -> Optional[Dict[str, Any]]:
    """
    Find an indicator by name in the configuration.
    
    Args:
        config: The loaded configuration
        name: Name of the indicator to find
        
    Returns:
        Dictionary with indicator details or None if not found
    """
    # Check lookback indicators
    for indicator in config.indicators.lookback:
        if indicator.name == name:
            return indicator.dict()
    
    # Check lookafter indicators
    for indicator in config.indicators.lookafter:
        if indicator.name == name:
            return indicator.dict()
    
    return None


def get_indicator_by_name_from_raw(raw_config: Dict[str, Any], name: str) -> Optional[Dict[str, Any]]:
    """
    Find an indicator by name in the raw configuration.
    
    Args:
        raw_config: The raw configuration dictionary
        name: Name of the indicator to find
        
    Returns:
        Dictionary with indicator details or None if not found
    """
    # Check lookback indicators
    for indicator in raw_config.get('indicators', {}).get('lookback', []):
        if indicator.get('name') == name:
            return indicator
    
    # Check lookafter indicators
    for indicator in raw_config.get('indicators', {}).get('lookafter', []):
        if indicator.get('name') == name:
            return indicator
    
    return None


def get_all_indicators(config: Config) -> List[BaseIndicator]:
    """
    Get all indicators from the configuration.
    
    Args:
        config: The loaded configuration
        
    Returns:
        List of all indicators
    """
    return config.indicators.lookback + config.indicators.lookafter


def get_x_columns(config: Config) -> List[Union[str, Dict[str, Any]]]:
    """
    Get the x_columns from the agent configuration.
    
    Args:
        config: The loaded configuration
        
    Returns:
        List of x_columns
    """
    return config.agent.distribution.x_columns 