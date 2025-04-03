import yaml
from typing import Dict, Any, Optional
from pathlib import Path
from .models import Config


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