import os
import pandas as pd
import pytest
from solvexity.analytic.pattern import Pattern

# Utility to get the path to the CSV file
def get_test_data_path(filename: str) -> str:
    return os.path.join(os.path.dirname(__file__), "data", filename)

@pytest.fixture
def btcusdt_df():
    path = get_test_data_path("BTCUSDT_1h.csv")
    return pd.read_csv(path)


