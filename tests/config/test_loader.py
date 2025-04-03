import pytest
import os
import tempfile
import yaml
from pathlib import Path
from typing import Dict, Any

from solvexity.config.loader import (
    load_config,
    get_indicator_by_name,
    get_indicator_by_name_from_raw,
    get_all_indicators,
    get_x_columns
)
from solvexity.config.models import Config, IndicatorType, IntervalType


@pytest.fixture
def sample_config_dict() -> Dict[str, Any]:
    """Create a sample configuration dictionary for testing."""
    return {
        "indicators": {
            "lookback": [
                {
                    "name": "returns_btcusdt_1m_30",
                    "type": "returns",
                    "symbol": "BTCUSDT",
                    "interval": "1m",
                    "period": 30
                },
                {
                    "name": "volatility_btcusdt_1m_30",
                    "type": "volatility",
                    "symbol": "BTCUSDT",
                    "interval": "1m",
                    "period": 30
                }
            ],
            "lookafter": [
                {
                    "name": "stopping_returns_btcusdt_1m_60",
                    "type": "stopping_return",
                    "symbol": "BTCUSDT",
                    "interval": "1m",
                    "period": 60,
                    "stop_loss": -0.06,
                    "stop_profit": 0.06
                }
            ]
        },
        "grpc": {
            "host": "0.0.0.0",
            "port": 50051,
            "timeout": 2,
            "max_workers": 10,
            "max_message_length": 1024
        },
        "redis": {
            "host": "localhost",
            "port": 6379,
            "db": 0,
            "password": ""
        },
        "agent": {
            "type": "qagent",
            "distribution": {
                "pipelines": [
                    {
                        "q": 0.05,
                        "path": "./models/qagent_0-05.pkl"
                    },
                    {
                        "q": 0.5,
                        "path": "./models/qagent_0-5.pkl"
                    },
                    {
                        "q": 0.95,
                        "path": "./models/qagent_0-95.pkl"
                    }
                ],
                "x_columns": [
                    "returns_btcusdt_1m_30",
                    "volatility_btcusdt_1m_30"
                ]
            }
        }
    }


@pytest.fixture
def sample_config_file(sample_config_dict) -> str:
    """Create a temporary YAML file with the sample configuration."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        yaml.dump(sample_config_dict, f)
        return f.name


@pytest.fixture
def sample_config_with_dict_x_columns(sample_config_dict) -> str:
    """Create a temporary YAML file with dictionary x_columns."""
    # Modify the x_columns to include a dictionary
    sample_config_dict["agent"]["distribution"]["x_columns"] = [
        "returns_btcusdt_1m_30",
        {
            "name": "custom_indicator",
            "type": "returns",
            "symbol": "BTCUSDT",
            "interval": "1m",
            "period": 30
        }
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        yaml.dump(sample_config_dict, f)
        return f.name


@pytest.fixture
def sample_config_with_nonexistent_x_columns(sample_config_dict) -> str:
    """Create a temporary YAML file with nonexistent x_columns."""
    # Add a nonexistent indicator to x_columns
    sample_config_dict["agent"]["distribution"]["x_columns"] = [
        "returns_btcusdt_1m_30",
        "nonexistent_indicator"
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        yaml.dump(sample_config_dict, f)
        return f.name


def test_load_config(sample_config_file):
    """Test loading a configuration file."""
    config = load_config(sample_config_file)
    
    assert isinstance(config, Config)
    assert len(config.indicators.lookback) == 2
    assert len(config.indicators.lookafter) == 1
    assert config.grpc.host == "0.0.0.0"
    assert config.redis.host == "localhost"
    assert config.agent.type == "qagent"
    assert len(config.agent.distribution.pipelines) == 3
    assert len(config.agent.distribution.x_columns) == 2


def test_load_config_with_dict_x_columns(sample_config_with_dict_x_columns):
    """Test loading a configuration file with dictionary x_columns."""
    config = load_config(sample_config_with_dict_x_columns)
    
    assert isinstance(config, Config)
    assert len(config.agent.distribution.x_columns) == 2
    
    # The first x_column should be resolved to a dictionary
    assert isinstance(config.agent.distribution.x_columns[0], dict)
    assert config.agent.distribution.x_columns[0]["name"] == "returns_btcusdt_1m_30"
    
    # The second x_column should remain a dictionary
    assert isinstance(config.agent.distribution.x_columns[1], dict)
    assert config.agent.distribution.x_columns[1]["name"] == "custom_indicator"


def test_load_config_with_nonexistent_x_columns(sample_config_with_nonexistent_x_columns):
    """Test loading a configuration file with nonexistent x_columns."""
    config = load_config(sample_config_with_nonexistent_x_columns)
    
    assert isinstance(config, Config)
    assert len(config.agent.distribution.x_columns) == 2
    
    # The first x_column should be resolved to a dictionary
    assert isinstance(config.agent.distribution.x_columns[0], dict)
    assert config.agent.distribution.x_columns[0]["name"] == "returns_btcusdt_1m_30"
    
    # The second x_column should remain a string since it doesn't exist
    assert isinstance(config.agent.distribution.x_columns[1], str)
    assert config.agent.distribution.x_columns[1] == "nonexistent_indicator"


@pytest.mark.parametrize("indicator_name,expected_type,expected_symbol", [
    ("returns_btcusdt_1m_30", "returns", "BTCUSDT"),
    ("volatility_btcusdt_1m_30", "volatility", "BTCUSDT"),
    ("nonexistent_indicator", None, None),
])
def test_get_indicator_by_name_parametrized(sample_config_file, indicator_name, expected_type, expected_symbol):
    """Test getting an indicator by name with different inputs."""
    config = load_config(sample_config_file)
    
    indicator = get_indicator_by_name(config, indicator_name)
    
    if expected_type is None:
        assert indicator is None
    else:
        assert indicator is not None
        assert indicator["name"] == indicator_name
        assert indicator["type"] == expected_type
        assert indicator["symbol"] == expected_symbol


def test_get_indicator_by_name_from_raw(sample_config_dict):
    """Test getting an indicator by name from raw configuration."""
    indicator = get_indicator_by_name_from_raw(sample_config_dict, "returns_btcusdt_1m_30")
    assert indicator is not None
    assert indicator["name"] == "returns_btcusdt_1m_30"
    assert indicator["type"] == "returns"
    assert indicator["symbol"] == "BTCUSDT"
    assert indicator["interval"] == "1m"
    assert indicator["period"] == 30
    
    indicator = get_indicator_by_name_from_raw(sample_config_dict, "nonexistent_indicator")
    assert indicator is None


def test_get_all_indicators(sample_config_file):
    """Test getting all indicators."""
    config = load_config(sample_config_file)
    
    indicators = get_all_indicators(config)
    assert len(indicators) == 3  # 2 lookback + 1 lookafter
    assert any(ind.name == "returns_btcusdt_1m_30" for ind in indicators)
    assert any(ind.name == "volatility_btcusdt_1m_30" for ind in indicators)
    assert any(ind.name == "stopping_returns_btcusdt_1m_60" for ind in indicators)


def test_get_x_columns(sample_config_file):
    """Test getting x_columns."""
    config = load_config(sample_config_file)
    
    x_columns = get_x_columns(config)
    assert len(x_columns) == 2
    
    # The x_columns should be resolved to dictionaries
    assert isinstance(x_columns[0], dict)
    assert x_columns[0]["name"] == "returns_btcusdt_1m_30"
    
    assert isinstance(x_columns[1], dict)
    assert x_columns[1]["name"] == "volatility_btcusdt_1m_30"


def test_load_config_file_not_found():
    """Test loading a configuration file that doesn't exist."""
    with pytest.raises(FileNotFoundError):
        load_config("nonexistent_file.yml")


def test_load_config_invalid_yaml():
    """Test loading an invalid YAML file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        f.write("invalid: yaml: content: {")
        f.flush()
        
        with pytest.raises(ValueError):
            load_config(f.name)


def test_load_config_invalid_structure():
    """Test loading a configuration file with invalid structure."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        yaml.dump({"invalid": "structure"}, f)
        f.flush()
        
        with pytest.raises(ValueError):
            load_config(f.name)


def test_cleanup(sample_config_file, sample_config_with_dict_x_columns, sample_config_with_nonexistent_x_columns):
    """Clean up temporary files."""
    os.unlink(sample_config_file)
    os.unlink(sample_config_with_dict_x_columns)
    os.unlink(sample_config_with_nonexistent_x_columns) 