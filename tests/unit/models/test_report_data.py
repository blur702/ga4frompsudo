"""
Tests for the ReportData model.
"""

import datetime
import pytest
from app.models.report_data import ReportData


def test_report_data_initialization():
    """Test the initialization of a ReportData instance with basic attributes."""
    # Setup a mock database object
    mock_db = object()
    
    # Test initialization with mandatory fields
    report_data = ReportData(
        database=mock_db,
        report_db_id=1,
        metric_name="pageviews"
    )
    
    # Assert the mandatory attributes are set correctly
    assert report_data.report_db_id == 1
    assert report_data.metric_name == "pageviews"
    assert report_data.metric_value is None
    assert report_data.property_ga4_id is None
    assert report_data.dimension_name is None
    assert report_data.dimension_value is None
    assert report_data.data_date is None
    assert report_data.id is None
    assert isinstance(report_data.data_timestamp, datetime.datetime)


def test_report_data_initialization_with_all_attributes():
    """Test the initialization of a ReportData instance with all attributes."""
    # Setup a mock database object
    mock_db = object()
    
    # Test datetime objects
    data_date = datetime.date(2023, 1, 1)
    data_timestamp = datetime.datetime(2023, 1, 1, 12, 0, 0)
    
    # Test initialization with all fields
    report_data = ReportData(
        database=mock_db,
        report_db_id=1,
        metric_name="pageviews",
        metric_value=1000,
        property_ga4_id="properties/12345",
        dimension_name="date",
        dimension_value="20230101",
        data_date=data_date,
        data_timestamp=data_timestamp,
        id_val=2
    )
    
    # Assert all attributes are set correctly
    assert report_data.report_db_id == 1
    assert report_data.metric_name == "pageviews"
    assert report_data.metric_value == "1000"  # Should be converted to string
    assert report_data.property_ga4_id == "properties/12345"
    assert report_data.dimension_name == "date"
    assert report_data.dimension_value == "20230101"
    assert report_data.data_date == data_date
    assert report_data.data_timestamp == data_timestamp
    assert report_data.id == 2


def test_report_data_initialization_with_string_dates():
    """Test the initialization of a ReportData instance with string date attributes."""
    # Setup a mock database object
    mock_db = object()
    
    # Test initialization with string dates
    report_data = ReportData(
        database=mock_db,
        report_db_id=1,
        metric_name="pageviews",
        data_date="2023-01-01",
        data_timestamp="2023-01-01T12:00:00"
    )
    
    # Assert the date attributes are parsed correctly
    assert isinstance(report_data.data_date, datetime.date)
    assert report_data.data_date.year == 2023
    assert report_data.data_date.month == 1
    assert report_data.data_date.day == 1
    
    assert isinstance(report_data.data_timestamp, datetime.datetime)
    assert report_data.data_timestamp.year == 2023
    assert report_data.data_timestamp.month == 1
    assert report_data.data_timestamp.day == 1
    assert report_data.data_timestamp.hour == 12


def test_report_data_initialization_with_invalid_report_db_id():
    """Test that initializing a ReportData with a None report_db_id raises ValueError."""
    # Setup a mock database object
    mock_db = object()
    
    # Test initialization with None report_db_id
    with pytest.raises(ValueError):
        ReportData(
            database=mock_db,
            report_db_id=None,
            metric_name="pageviews"
        )


def test_report_data_initialization_with_invalid_metric_name():
    """Test that initializing a ReportData with an empty metric_name raises ValueError."""
    # Setup a mock database object
    mock_db = object()
    
    # Test initialization with empty metric_name
    with pytest.raises(ValueError):
        ReportData(
            database=mock_db,
            report_db_id=1,
            metric_name=""
        )


def test_report_data_to_dict():
    """Test that _to_dict converts the ReportData attributes to a dictionary correctly."""
    # Setup a mock database object
    mock_db = object()
    
    # Create a ReportData instance with all attributes
    data_date = datetime.date(2023, 1, 1)
    data_timestamp = datetime.datetime(2023, 1, 1, 12, 0, 0)
    
    report_data = ReportData(
        database=mock_db,
        report_db_id=1,
        metric_name="pageviews",
        metric_value=1000,
        property_ga4_id="properties/12345",
        dimension_name="date",
        dimension_value="20230101",
        data_date=data_date,
        data_timestamp=data_timestamp,
        id_val=2
    )
    
    # Call _to_dict
    result = report_data._to_dict()
    
    # Assert the dictionary has the correct keys and values
    assert result["report_db_id"] == 1
    assert result["metric_name"] == "pageviews"
    assert result["metric_value"] == "1000"  # Stored as string
    assert result["property_ga4_id"] == "properties/12345"
    assert result["dimension_name"] == "date"
    assert result["dimension_value"] == "20230101"
    assert result["data_date"] == "2023-01-01"  # ISO format
    assert result["data_timestamp"] == data_timestamp.isoformat()
    # id should not be in the dictionary as it's handled by BaseModel
    assert "id" not in result


def test_report_data_from_db_row():
    """Test that _from_db_row creates a ReportData instance from a database row."""
    # Setup a mock database object
    mock_db = object()
    
    # Create a mock database row (dictionary)
    row_dict = {
        "id": 2,
        "report_db_id": 1,
        "metric_name": "pageviews",
        "metric_value": "1000",
        "property_ga4_id": "properties/12345",
        "dimension_name": "date",
        "dimension_value": "20230101",
        "data_date": "2023-01-01",
        "data_timestamp": "2023-01-01T12:00:00"
    }
    
    # Call _from_db_row
    report_data = ReportData._from_db_row(row_dict, mock_db)
    
    # Assert the ReportData instance has the correct attributes
    assert report_data.id == 2
    assert report_data.report_db_id == 1
    assert report_data.metric_name == "pageviews"
    assert report_data.metric_value == "1000"
    assert report_data.property_ga4_id == "properties/12345"
    assert report_data.dimension_name == "date"
    assert report_data.dimension_value == "20230101"
    assert isinstance(report_data.data_date, datetime.date)
    assert report_data.data_date.year == 2023
    assert report_data.data_date.month == 1
    assert report_data.data_date.day == 1
    assert isinstance(report_data.data_timestamp, datetime.datetime)
    assert report_data.data_timestamp.year == 2023
    assert report_data.data_timestamp.month == 1
    assert report_data.data_timestamp.day == 1
    assert report_data.data_timestamp.hour == 12


def test_report_data_repr():
    """Test the string representation of a ReportData instance."""
    # Setup a mock database object
    mock_db = object()
    
    # Create a ReportData instance
    data_date = datetime.date(2023, 1, 1)
    report_data = ReportData(
        database=mock_db,
        report_db_id=1,
        metric_name="pageviews",
        metric_value=1000,
        data_date=data_date,
        id_val=2
    )
    
    # Get the string representation
    repr_str = repr(report_data)
    
    # Assert the string representation contains the essential attributes
    assert "ReportData" in repr_str
    assert "id=2" in repr_str
    assert "report_db_id=1" in repr_str
    assert "metric='pageviews'" in repr_str
    assert "'1000'" in repr_str
    assert "date='2023-01-01'" in repr_str