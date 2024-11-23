import pytest
from unittest.mock import patch, MagicMock
from service import ServiceFactory


@pytest.fixture
def services_config():
    return {
        "binance_primary": {
            "factory": "binance",
            "api_key": "PRIMARY_API_KEY",
            "api_secret": "PRIMARY_API_SECRET"
        },
        "redis": {
            "factory": "redis",
            "host": "localhost",
            "port": 6379,
            "db": 0
        },
        "notify": {
            "factory": "notify",
            "webhook": "https://example.com/webhook"
        },
        "tcp": {
            "factory": "tcp",
            "host": "localhost",
            "port": 8080
        }
    }


@pytest.fixture
def service_factory(services_config):
    return ServiceFactory(services_config)


@patch("service.service_factory.FACTORY_REGISTRY", {
    "redis": MagicMock(return_value="Mocked Redis Instance"),
    "binance": MagicMock(return_value="Mocked Binance Client"),
    "notify": MagicMock(return_value="Mocked Notification Instance"),
    "tcp": MagicMock(return_value="Mocked TCP Socket")
})
def test_get_redis_service(service_factory):
    redis_service = service_factory["redis"]
    assert redis_service == "Mocked Redis Instance"


@patch("service.service_factory.FACTORY_REGISTRY", {
    "redis": MagicMock(return_value="Mocked Redis Instance"),
    "binance": MagicMock(return_value="Mocked Binance Client"),
    "notify": MagicMock(return_value="Mocked Notification Instance"),
    "tcp": MagicMock(return_value="Mocked TCP Socket")
})
def test_get_binance_service(service_factory):
    binance_service = service_factory["binance_primary"]
    assert binance_service == "Mocked Binance Client"


@patch("service.service_factory.FACTORY_REGISTRY", {
    "redis": MagicMock(return_value="Mocked Redis Instance"),
    "binance": MagicMock(return_value="Mocked Binance Client"),
    "notify": MagicMock(return_value="Mocked Notification Instance"),
    "tcp": MagicMock(return_value="Mocked TCP Socket")
})
def test_get_notification_service(service_factory):
    notification_service = service_factory["notify"]
    assert notification_service == "Mocked Notification Instance"


@patch("service.service_factory.FACTORY_REGISTRY", {
    "redis": MagicMock(return_value="Mocked Redis Instance"),
    "binance": MagicMock(return_value="Mocked Binance Client"),
    "notify": MagicMock(return_value="Mocked Notification Instance"),
    "tcp": MagicMock(return_value="Mocked TCP Socket")
})
def test_get_tcp_service(service_factory):
    tcp_service = service_factory["tcp"]
    assert tcp_service == "Mocked TCP Socket"


def test_unknown_service(service_factory):
    with pytest.raises(ValueError, match="Service 'unknown_service' not found in the configuration."):
        service_factory["unknown_service"]
