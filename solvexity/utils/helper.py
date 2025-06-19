import re
from typing import Union


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
