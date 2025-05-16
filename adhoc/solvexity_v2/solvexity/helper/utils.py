import json

def load_config(file_path):
    try:
        with open(file_path, 'r') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        raise
    except Exception as e:
        raise


def to_ms_interval(interval_str: str) -> int:
    # Define mappings for time units to seconds
    unit_mappings = {
        's': 1_000,         # seconds
        'm': 60_000,        # minutes
        'h': 3_600_000,      # hours
        'd': 86_400_000,     # days
    }
    
    # Extract the numeric part and the unit part
    try:
        value = int(interval_str[:-1])  # Get the number (e.g., 5 from '5m')
        unit = interval_str[-1]         # Get the unit character (e.g., 'm' from '5m')
        
        if unit in unit_mappings:
            return value * unit_mappings[unit]
        else:
            raise ValueError("Invalid time unit. Use 's', 'm', 'h', or 'd'.")
    
    except (ValueError, IndexError):
        raise ValueError("Invalid interval format. Please use formats like '1s', '5m', '1h', '5d'.")