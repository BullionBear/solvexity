import time
import functools
from typing import Dict, Any, Callable, Optional
from collections import defaultdict


class MethodTracker:
    """
    A portable tracker for method calls and execution time.
    
    This class provides decorators and methods to track:
    - Number of method calls
    - Total elapsed time per method
    - Average elapsed time per method
    
    Usage:
        tracker = MethodTracker()
        
        # Decorate methods you want to track
        @tracker.track
        def my_method():
            # Method implementation
            pass
            
        # Get summary of tracked methods
        summary = tracker.get_summary()
    """
    
    def __init__(self):
        self._call_counts = defaultdict(int)
        self._total_elapsed = defaultdict(float)
        self._enabled = True
    
    def track(self, func: Callable) -> Callable:
        """
        Decorator to track method calls and execution time.
        
        Args:
            func: The function to track
            
        Returns:
            Wrapped function that tracks calls and execution time
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not self._enabled:
                return func(*args, **kwargs)
                
            method_name = f"{func.__module__}.{func.__name__}"
            self._call_counts[method_name] += 1
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                elapsed = time.time() - start_time
                self._total_elapsed[method_name] += elapsed
                
        return wrapper
    
    def enable(self) -> None:
        """Enable tracking."""
        self._enabled = True
    
    def disable(self) -> None:
        """Disable tracking."""
        self._enabled = False
    
    def reset(self) -> None:
        """Reset all tracking data."""
        self._call_counts.clear()
        self._total_elapsed.clear()
    
    def get_summary(self) -> Dict[str, Dict[str, Any]]:
        """
        Get a summary of all tracked methods.
        
        Returns:
            Dictionary with method names as keys and tracking data as values
        """
        summary = {}
        for method_name in self._call_counts:
            call_count = self._call_counts[method_name]
            total_elapsed = self._total_elapsed[method_name]
            avg_elapsed = total_elapsed / call_count if call_count > 0 else 0
            
            summary[method_name] = {
                "calls": call_count,
                "total_elapsed": total_elapsed,
                "avg_elapsed": avg_elapsed
            }
        
        return summary
    
    def print_summary(self) -> None:
        """Print a formatted summary of all tracked methods."""
        summary = self.get_summary()
        
        if not summary:
            print("No tracked methods found.")
            return
            
        print("\nMethod Tracking Summary:")
        print("-" * 80)
        print(f"{'Method':<50} {'Calls':<10} {'Total Time (s)':<15} {'Avg Time (s)':<15}")
        print("-" * 80)
        
        for method_name, data in sorted(summary.items()):
            print(f"{method_name:<50} {data['calls']:<10} {data['total_elapsed']:<15.6f} {data['avg_elapsed']:<15.6f}")
        
        print("-" * 80) 