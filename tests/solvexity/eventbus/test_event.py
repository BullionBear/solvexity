import pytest

from solvexity.eventbus.event import Event



class TestEventInitialization:
    """Test Event initialization and validation."""
    
    def test_event_creation(self):
        """Test creating a basic event."""
        data = {"value": "test_value", "number": 42}
        event = Event(
            time_ms=1234567890,
            data=data
        )
        
        assert event.time_ms == 1234567890
        assert event.data == data
        assert event.data["value"] == "test_value"
        assert event.data["number"] == 42
        assert event.uid is not None  # uid should be auto-generated
    
    def test_event_with_minimal_data(self):
        """Test creating an event with minimal data."""
        data = {"value": "minimal"}
        event = Event(
            time_ms=1234567890,
            data=data
        )
        
        assert event.time_ms == 1234567890
        assert event.data["value"] == "minimal"
        assert event.uid is not None  # uid should be auto-generated
    
    def test_event_validation(self):
        """Test that Event validates required fields."""
        # Missing required fields should raise validation error
        with pytest.raises(ValueError):
            Event(
                time_ms=1234567890,
                # Missing data
            )
    
    def test_event_data_validation(self):
        """Test that Event validates data field."""
        # Event accepts any type of data (data: Any)
        # This should work with dict data
        event = Event(
            time_ms=1234567890,
            data={"value": "test_value"}  # Dict data
        )
        
        # The data should be a dict
        assert isinstance(event.data, dict)
        assert event.data["value"] == "test_value"


class TestEventProperties:
    """Test Event properties and methods."""
    
    def test_event_equality(self):
        """Test event equality."""
        data1 = {"value": "test", "number": 1}
        data2 = {"value": "test", "number": 1}
        
        event1 = Event(
            time_ms=1234567890,
            data=data1
        )
        
        event2 = Event(
            time_ms=1234567890,
            data=data2
        )
        
        # Events with same data but different uids should not be equal
        assert event1 != event2
    
    def test_event_inequality(self):
        """Test event inequality."""
        data1 = {"value": "test1", "number": 1}
        data2 = {"value": "test2", "number": 1}
        
        event1 = Event(
            time_ms=1234567890,
            data=data1
        )
        
        event2 = Event(
            time_ms=1234567890,
            data=data2
        )
        
        assert event1 != event2
    
    def test_event_repr(self):
        """Test event string representation."""
        data = {"value": "test_value", "number": 42}
        event = Event(
            time_ms=1234567890,
            data=data
        )
        
        repr_str = repr(event)
        assert "Event" in repr_str
        assert "time_ms=1234567890" in repr_str
        assert "uid=" in repr_str


class TestEventEdgeCases:
    """Test Event edge cases and boundary conditions."""
    
    def test_event_with_zero_timestamp(self):
        """Test event with zero timestamp."""
        data = {"value": "test"}
        event = Event(
            time_ms=0,
            data=data
        )
        
        assert event.time_ms == 0
    
    def test_event_with_negative_timestamp(self):
        """Test event with negative timestamp."""
        data = {"value": "test"}
        event = Event(
            time_ms=-1234567890,
            data=data
        )
        
        assert event.time_ms == -1234567890
    
    def test_event_with_default_values(self):
        """Test event with default values."""
        data = {"value": "test"}
        event = Event(data=data)
        
        assert event.time_ms is not None
        assert event.uid is not None
    
    def test_event_with_unicode_data(self):
        """Test event with unicode data."""
        data = {"value": "测试数据", "unicode": "🎉"}
        event = Event(
            time_ms=1234567890,
            data=data
        )
        
        assert event.data["value"] == "测试数据"
        assert event.data["unicode"] == "🎉"


class TestEventDataTypes:
    """Test Event with different data types."""
    
    def test_event_with_complex_data(self):
        """Test event with complex nested data."""
        data = {
            "name": "complex_test",
            "items": ["item1", "item2", "item3"],
            "metadata": {"key1": "value1", "key2": "value2"}
        }
        
        event = Event(
            time_ms=1234567890,
            data=data
        )
        
        assert event.data["name"] == "complex_test"
        assert len(event.data["items"]) == 3
        assert event.data["metadata"]["key1"] == "value1"
    
    def test_event_with_numeric_data(self):
        """Test event with numeric data."""
        data = {
            "integer": 42,
            "float_val": 3.14159,
            "boolean": True
        }
        
        event = Event(
            time_ms=1234567890,
            data=data
        )
        
        assert event.data["integer"] == 42
        assert event.data["float_val"] == 3.14159
        assert event.data["boolean"] is True
