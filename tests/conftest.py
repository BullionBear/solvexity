import pytest
import os
import sys
from pathlib import Path

# Add the project root directory to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

# Configure pytest
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    ) 