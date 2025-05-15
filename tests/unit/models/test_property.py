"""
Tests for the Property model.
"""

import datetime
import pytest
from app.models.property import Property


def test_property_initialization():
    """Test the initialization of a Property instance with basic attributes."""
    # Setup a mock database object
    mock_db = object()
    
    # Test initialization with mandatory fields
    prop = Property(
        database=mock_db,
        property_id="properties/12345"
    )
    
    # Assert the mandatory attributes are set correctly
    assert prop.property_id == "properties/12345"
    assert prop.property_name is None
    assert prop.account_id is None
    assert prop.create_time is None
    assert prop.update_time is None
    assert prop.id is None


def test_property_initialization_with_all_attributes():
    """Test the initialization of a Property instance with all attributes."""
    # Setup a mock database object
    mock_db = object()
    
    # Test datetime objects
    create_time = datetime.datetime(2023, 1, 1, 12, 0, 0)
    update_time = datetime.datetime(2023, 1, 2, 12, 0, 0)
    
    # Test initialization with all fields
    prop = Property(
        database=mock_db,
        property_id="properties/12345",
        property_name="Test Property",
        account_id="accounts/67890",
        create_time=create_time,
        update_time=update_time,
        id_val=1
    )
    
    # Assert all attributes are set correctly
    assert prop.property_id == "properties/12345"
    assert prop.property_name == "Test Property"
    assert prop.account_id == "accounts/67890"
    assert prop.create_time == create_time
    assert prop.update_time == update_time
    assert prop.id == 1


def test_property_initialization_with_string_dates():
    """Test the initialization of a Property instance with string date attributes."""
    # Setup a mock database object
    mock_db = object()
    
    # Test initialization with string dates
    prop = Property(
        database=mock_db,
        property_id="properties/12345",
        create_time="2023-01-01T12:00:00",
        update_time="2023-01-02T12:00:00"
    )
    
    # Assert the date attributes are parsed correctly
    assert isinstance(prop.create_time, datetime.datetime)
    assert isinstance(prop.update_time, datetime.datetime)
    assert prop.create_time.year == 2023
    assert prop.create_time.month == 1
    assert prop.create_time.day == 1
    assert prop.create_time.hour == 12
    assert prop.update_time.year == 2023
    assert prop.update_time.month == 1
    assert prop.update_time.day == 2
    assert prop.update_time.hour == 12


def test_property_initialization_with_invalid_id():
    """Test that initializing a Property with an empty property_id raises ValueError."""
    # Setup a mock database object
    mock_db = object()
    
    # Test initialization with empty property_id
    with pytest.raises(ValueError):
        Property(
            database=mock_db,
            property_id=""
        )


def test_property_to_dict():
    """Test that _to_dict converts the Property attributes to a dictionary correctly."""
    # Setup a mock database object
    mock_db = object()
    
    # Create a Property instance with all attributes
    create_time = datetime.datetime(2023, 1, 1, 12, 0, 0)
    update_time = datetime.datetime(2023, 1, 2, 12, 0, 0)
    
    prop = Property(
        database=mock_db,
        property_id="properties/12345",
        property_name="Test Property",
        account_id="accounts/67890",
        create_time=create_time,
        update_time=update_time,
        id_val=1
    )
    
    # Call _to_dict
    result = prop._to_dict()
    
    # Assert the dictionary has the correct keys and values
    assert result["property_id"] == "properties/12345"
    assert result["property_name"] == "Test Property"
    assert result["account_id"] == "accounts/67890"
    assert result["create_time"] == create_time.isoformat()
    assert result["update_time"] == update_time.isoformat()
    # id should not be in the dictionary as it's handled by BaseModel
    assert "id" not in result


def test_property_from_db_row():
    """Test that _from_db_row creates a Property instance from a database row."""
    # Setup a mock database object
    mock_db = object()
    
    # Create a mock database row (dictionary)
    row_dict = {
        "id": 1,
        "property_id": "properties/12345",
        "property_name": "Test Property",
        "account_id": "accounts/67890",
        "create_time": "2023-01-01T12:00:00",
        "update_time": "2023-01-02T12:00:00"
    }
    
    # Call _from_db_row
    prop = Property._from_db_row(row_dict, mock_db)
    
    # Assert the Property instance has the correct attributes
    assert prop.id == 1
    assert prop.property_id == "properties/12345"
    assert prop.property_name == "Test Property"
    assert prop.account_id == "accounts/67890"
    assert isinstance(prop.create_time, datetime.datetime)
    assert isinstance(prop.update_time, datetime.datetime)
    assert prop.create_time.year == 2023
    assert prop.create_time.month == 1
    assert prop.create_time.day == 1
    assert prop.create_time.hour == 12
    assert prop.update_time.year == 2023
    assert prop.update_time.month == 1
    assert prop.update_time.day == 2
    assert prop.update_time.hour == 12


def test_property_repr():
    """Test the string representation of a Property instance."""
    # Setup a mock database object
    mock_db = object()
    
    # Create a Property instance
    prop = Property(
        database=mock_db,
        property_id="properties/12345",
        property_name="Test Property",
        account_id="accounts/67890",
        id_val=1
    )
    
    # Get the string representation
    repr_str = repr(prop)
    
    # Assert the string representation contains the essential attributes
    assert "Property" in repr_str
    assert "id=1" in repr_str
    assert "property_id='properties/12345'" in repr_str
    assert "name='Test Property'" in repr_str
    assert "account_id='accounts/67890'" in repr_str