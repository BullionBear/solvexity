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

def test_recognize_support(btcusdt_df):
    result = Pattern.recognize("support", btcusdt_df)
    assert isinstance(result, dict)
    assert "support" in result
    assert isinstance(result["support"], float)

def test_recognize_resistance(btcusdt_df):
    result = Pattern.recognize("resistance", btcusdt_df)
    assert isinstance(result, dict)
    assert "resistance" in result
    assert isinstance(result["resistance"], float)

def test_recognize_invalid_method(btcusdt_df):
    with pytest.raises(ValueError, match="Method .* not supported"):
        Pattern.recognize("invalid_method", btcusdt_df)
