import re
from typing import Union
from hooklet.logger.hooklet_logger import LogFormat 
from solvexity.logger import SolvexityLoggerConfig

def str_to_ms(time_str: str) -> int:
    """
    Convert time string to milliseconds.
    
    Supports formats like:
    - "1m", "5m", "30m" (minutes)
    - "1h", "2h" (hours) 
    - "1d" (days)
    
    Args:
        time_str: Time string in format like "1m", "5m", "30m", "1h", "2h", "1d"
        
    Returns:
        Time in milliseconds
        
    Raises:
        ValueError: If the time string format is invalid or unsupported
    """
    if not time_str or not isinstance(time_str, str):
        raise ValueError("Time string must be a non-empty string")
    
    # Remove any whitespace
    time_str = time_str.strip()
    
    # Pattern to match: number followed by unit (m, h, d)
    pattern = r'^(\d+)([mhd])$'
    match = re.match(pattern, time_str)
    
    if not match:
        raise ValueError(f"Invalid time format: {time_str}. Expected format like '1m', '5m', '30m', '1h', '2h', '1d'")
    
    value = int(match.group(1))
    unit = match.group(2)
    
    # Convert to milliseconds
    if unit == 'm':  # minutes
        return value * 60 * 1000
    elif unit == 'h':  # hours
        return value * 60 * 60 * 1000
    elif unit == 'd':  # days
        return value * 24 * 60 * 60 * 1000
    else:
        raise ValueError(f"Unsupported time unit: {unit}. Supported units: m (minutes), h (hours), d (days)")


def ms_to_str(ms: int) -> str:
    """
    Convert milliseconds to the most appropriate time string format.
    
    Args:
        ms: Time in milliseconds
        
    Returns:
        Time string in format like "1m", "5m", "30m", "1h", "2h", "1d"
    """
    if ms < 0:
        raise ValueError("Milliseconds must be non-negative")
    
    # Convert to seconds first
    seconds = ms // 1000
    
    # Convert to days
    days = seconds // (24 * 60 * 60)
    if days > 0:
        return f"{days}d"
    
    # Convert to hours
    hours = seconds // (60 * 60)
    if hours > 0:
        return f"{hours}h"
    
    # Convert to minutes
    minutes = seconds // 60
    if minutes > 0:
        return f"{minutes}m"
    
    # If less than 1 minute, return in seconds
    return f"{seconds}s"

def str_to_bytes(byte_str: str) -> int:
    """
    Convert bytes representation to int.
    
    Args:
        byte_str: Bytes representation in format like "100B", "100KB", "100MB", "100GB"
        
    Returns:
        Bytes in int
    """
    if not byte_str or not isinstance(byte_str, str):
        raise ValueError("Byte string must be a non-empty string")
    
    # Remove any whitespace
    byte_str = byte_str.strip()
    
    # Pattern to match: number followed by unit (B, KB, MB, GB)
    pattern = r'^(\d+)([BKMGT]B)$'
    match = re.match(pattern, byte_str)
    
    if not match:
        raise ValueError(f"Invalid byte format: {byte_str}. Expected format like '100B', '100KB', '100MB', '100GB'")
    
    value = int(match.group(1))
    unit = match.group(2)
    
    # Convert to bytes
    if unit == 'B':  # bytes
        return value
    elif unit == 'KB':  # kilobytes
        return value * 1024
    elif unit == 'MB':  # megabytes
        return value * 1024 * 1024
    elif unit == 'GB':  # gigabytes
        return value * 1024 * 1024 * 1024
    else:
        raise ValueError(f"Unsupported byte unit: {unit}. Supported units: B, KB, MB, GB")
    
def bytes_to_str(bytes: int) -> str:
    """
    Convert bytes to the most appropriate byte string format.
    
    Args:
        bytes: Bytes

    Returns:
        Byte string in format like "100B", "100KB", "100MB", "100GB"
    """
    if bytes < 0:
        raise ValueError("Bytes must be non-negative")
    
    # Convert to bytes
    if bytes < 1024:
        return f"{bytes}B"
    elif bytes < 1024 * 1024:
        return f"{bytes / 1024}KB"
    elif bytes < 1024 * 1024 * 1024:
        return f"{bytes / 1024 / 1024}MB"
    else:
        return f"{bytes / 1024 / 1024 / 1024}GB"
    
def str_to_log_format(log_format: str) -> LogFormat:
    """
    Convert string to LogFormat.
    
    Args:
        log_format: Log format string
        
    Returns:
        LogFormat
    """
    if log_format == "detailed":
        return LogFormat.DETAILED
    elif log_format == "simple":
        return LogFormat.SIMPLE
    elif log_format == "json":
        return LogFormat.JSON
    else:
        raise ValueError(f"Invalid log format: {log_format}. Expected format like 'detailed', 'simple', 'json'")
    
def to_logger_config(config: dict) -> SolvexityLoggerConfig:
    """
    Convert config to SolvexityLoggerConfig.
    
    Args:
        config: Config
        
    Returns:
        SolvexityLoggerConfig
    """
    return SolvexityLoggerConfig(
        level=config.get("level", "INFO"),
        format_type=str_to_log_format(config.get("format_type", "detailed")),
        log_file=config.get("log_file", "logs/app.log"),
        rotation=config.get("rotation", True),
        max_backup=config.get("max_backup", 10)
    )