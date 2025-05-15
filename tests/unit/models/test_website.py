"""
Tests for the Website model.
"""

import datetime
import pytest
from app.models.website import Website


def test_website_initialization():
    """Test the initialization of a Website instance with basic attributes."""
    # Setup a mock database object
    mock_db = object()
    
    # Test initialization with mandatory fields
    website = Website(
        database=mock_db,
        website_id="properties/12345/dataStreams/456",
        property_db_id=1
    )
    
    # Assert the mandatory attributes are set correctly
    assert website.website_id == "properties/12345/dataStreams/456"
    assert website.property_db_id == 1
    assert website.website_url is None
    assert website.create_time is None
    assert website.update_time is None
    assert website.id is None


def test_website_initialization_with_all_attributes():
    """Test the initialization of a Website instance with all attributes."""
    # Setup a mock database object
    mock_db = object()
    
    # Test datetime objects
    create_time = datetime.datetime(2023, 1, 1, 12, 0, 0)
    update_time = datetime.datetime(2023, 1, 2, 12, 0, 0)
    
    # Test initialization with all fields
    website = Website(
        database=mock_db,
        website_id="properties/12345/dataStreams/456",
        property_db_id=1,
        website_url="https://example.com",
        create_time=create_time,
        update_time=update_time,
        id_val=2
    )
    
    # Assert all attributes are set correctly
    assert website.website_id == "properties/12345/dataStreams/456"
    assert website.property_db_id == 1
    assert website.website_url == "https://example.com"
    assert website.create_time == create_time
    assert website.update_time == update_time
    assert website.id == 2


def test_website_initialization_with_string_dates():
    """Test the initialization of a Website instance with string date attributes."""
    # Setup a mock database object
    mock_db = object()
    
    # Test initialization with string dates
    website = Website(
        database=mock_db,
        website_id="properties/12345/dataStreams/456",
        property_db_id=1,
        create_time="2023-01-01T12:00:00",
        update_time="2023-01-02T12:00:00"
    )
    
    # Assert the date attributes are parsed correctly
    assert isinstance(website.create_time, datetime.datetime)
    assert isinstance(website.update_time, datetime.datetime)
    assert website.create_time.year == 2023
    assert website.create_time.month == 1
    assert website.create_time.day == 1
    assert website.create_time.hour == 12
    assert website.update_time.year == 2023
    assert website.update_time.month == 1
    assert website.update_time.day == 2
    assert website.update_time.hour == 12


def test_website_initialization_with_invalid_id():
    """Test that initializing a Website with an empty website_id raises ValueError."""
    # Setup a mock database object
    mock_db = object()
    
    # Test initialization with empty website_id
    with pytest.raises(ValueError):
        Website(
            database=mock_db,
            website_id="",
            property_db_id=1
        )


def test_website_initialization_with_invalid_property_db_id():
    """Test that initializing a Website with a None property_db_id raises ValueError."""
    # Setup a mock database object
    mock_db = object()
    
    # Test initialization with None property_db_id
    with pytest.raises(ValueError):
        Website(
            database=mock_db,
            website_id="properties/12345/dataStreams/456",
            property_db_id=None
        )


def test_website_to_dict():
    """Test that _to_dict converts the Website attributes to a dictionary correctly."""
    # Setup a mock database object
    mock_db = object()
    
    # Create a Website instance with all attributes
    create_time = datetime.datetime(2023, 1, 1, 12, 0, 0)
    update_time = datetime.datetime(2023, 1, 2, 12, 0, 0)
    
    website = Website(
        database=mock_db,
        website_id="properties/12345/dataStreams/456",
        property_db_id=1,
        website_url="https://example.com",
        create_time=create_time,
        update_time=update_time,
        id_val=2
    )
    
    # Call _to_dict
    result = website._to_dict()
    
    # Assert the dictionary has the correct keys and values
    assert result["website_id"] == "properties/12345/dataStreams/456"
    assert result["property_db_id"] == 1
    assert result["website_url"] == "https://example.com"
    assert result["create_time"] == create_time.isoformat()
    assert result["update_time"] == update_time.isoformat()
    # id should not be in the dictionary as it's handled by BaseModel
    assert "id" not in result


def test_website_from_db_row():
    """Test that _from_db_row creates a Website instance from a database row."""
    # Setup a mock database object
    mock_db = object()
    
    # Create a mock database row (dictionary)
    row_dict = {
        "id": 2,
        "website_id": "properties/12345/dataStreams/456",
        "property_db_id": 1,
        "website_url": "https://example.com",
        "create_time": "2023-01-01T12:00:00",
        "update_time": "2023-01-02T12:00:00"
    }
    
    # Call _from_db_row
    website = Website._from_db_row(row_dict, mock_db)
    
    # Assert the Website instance has the correct attributes
    assert website.id == 2
    assert website.website_id == "properties/12345/dataStreams/456"
    assert website.property_db_id == 1
    assert website.website_url == "https://example.com"
    assert isinstance(website.create_time, datetime.datetime)
    assert isinstance(website.update_time, datetime.datetime)
    assert website.create_time.year == 2023
    assert website.create_time.month == 1
    assert website.create_time.day == 1
    assert website.create_time.hour == 12
    assert website.update_time.year == 2023
    assert website.update_time.month == 1
    assert website.update_time.day == 2
    assert website.update_time.hour == 12


def test_website_repr():
    """Test the string representation of a Website instance."""
    # Setup a mock database object
    mock_db = object()
    
    # Create a Website instance
    website = Website(
        database=mock_db,
        website_id="properties/12345/dataStreams/456",
        property_db_id=1,
        website_url="https://example.com",
        id_val=2
    )
    
    # Get the string representation
    repr_str = repr(website)
    
    # Assert the string representation contains the essential attributes
    assert "Website" in repr_str
    assert "id=2" in repr_str
    assert "website_id='properties/12345/dataStreams/456'" in repr_str
    assert "url='https://example.com'" in repr_str
    assert "property_db_id=1" in repr_str