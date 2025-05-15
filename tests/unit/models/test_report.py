"""
Tests for the Report model.
"""

import datetime
import json
import pytest
from app.models.report import Report


def test_report_initialization():
    """Test the initialization of a Report instance with basic attributes."""
    # Setup a mock database object
    mock_db = object()
    
    # Test initialization with mandatory fields
    report = Report(
        database=mock_db,
        report_name="Test Report",
        report_type="traffic_analysis"
    )
    
    # Assert the mandatory attributes are set correctly
    assert report.report_name == "Test Report"
    assert report.report_type == "traffic_analysis"
    assert report.parameters == {}
    assert report.status == "pending"
    assert report.file_path is None
    assert report.id is None
    assert isinstance(report.create_time, datetime.datetime)


def test_report_initialization_with_all_attributes():
    """Test the initialization of a Report instance with all attributes."""
    # Setup a mock database object
    mock_db = object()
    
    # Test datetime objects
    create_time = datetime.datetime(2023, 1, 1, 12, 0, 0)
    parameters = {"date_range": "last-30-days", "metrics": ["pageviews", "sessions"]}
    
    # Test initialization with all fields
    report = Report(
        database=mock_db,
        report_name="Test Report",
        report_type="traffic_analysis",
        parameters=parameters,
        create_time=create_time,
        status="completed",
        file_path="/path/to/report.pdf",
        id_val=1
    )
    
    # Assert all attributes are set correctly
    assert report.report_name == "Test Report"
    assert report.report_type == "traffic_analysis"
    assert report.parameters == parameters
    assert report.create_time == create_time
    assert report.status == "completed"
    assert report.file_path == "/path/to/report.pdf"
    assert report.id == 1


def test_report_initialization_with_string_date():
    """Test the initialization of a Report instance with string date attribute."""
    # Setup a mock database object
    mock_db = object()
    
    # Test initialization with string dates
    report = Report(
        database=mock_db,
        report_name="Test Report",
        report_type="traffic_analysis",
        create_time="2023-01-01T12:00:00"
    )
    
    # Assert the date attribute is parsed correctly
    assert isinstance(report.create_time, datetime.datetime)
    assert report.create_time.year == 2023
    assert report.create_time.month == 1
    assert report.create_time.day == 1
    assert report.create_time.hour == 12


def test_report_initialization_with_invalid_name():
    """Test that initializing a Report with an empty report_name raises ValueError."""
    # Setup a mock database object
    mock_db = object()
    
    # Test initialization with empty report_name
    with pytest.raises(ValueError):
        Report(
            database=mock_db,
            report_name="",
            report_type="traffic_analysis"
        )


def test_report_initialization_with_invalid_type():
    """Test that initializing a Report with an empty report_type raises ValueError."""
    # Setup a mock database object
    mock_db = object()
    
    # Test initialization with empty report_type
    with pytest.raises(ValueError):
        Report(
            database=mock_db,
            report_name="Test Report",
            report_type=""
        )


def test_report_to_dict():
    """Test that _to_dict converts the Report attributes to a dictionary correctly."""
    # Setup a mock database object
    mock_db = object()
    
    # Create a Report instance with all attributes
    create_time = datetime.datetime(2023, 1, 1, 12, 0, 0)
    parameters = {"date_range": "last-30-days", "metrics": ["pageviews", "sessions"]}
    
    report = Report(
        database=mock_db,
        report_name="Test Report",
        report_type="traffic_analysis",
        parameters=parameters,
        create_time=create_time,
        status="completed",
        file_path="/path/to/report.pdf",
        id_val=1
    )
    
    # Call _to_dict
    result = report._to_dict()
    
    # Assert the dictionary has the correct keys and values
    assert result["report_name"] == "Test Report"
    assert result["report_type"] == "traffic_analysis"
    assert json.loads(result["parameters"]) == parameters
    assert result["create_time"] == create_time.isoformat()
    assert result["status"] == "completed"
    assert result["file_path"] == "/path/to/report.pdf"
    # id should not be in the dictionary as it's handled by BaseModel
    assert "id" not in result


def test_report_from_db_row():
    """Test that _from_db_row creates a Report instance from a database row."""
    # Setup a mock database object
    mock_db = object()
    
    # Create a mock database row (dictionary)
    parameters_json = json.dumps({"date_range": "last-30-days", "metrics": ["pageviews", "sessions"]})
    row_dict = {
        "id": 1,
        "report_name": "Test Report",
        "report_type": "traffic_analysis",
        "parameters": parameters_json,
        "create_time": "2023-01-01T12:00:00",
        "status": "completed",
        "file_path": "/path/to/report.pdf"
    }
    
    # Call _from_db_row
    report = Report._from_db_row(row_dict, mock_db)
    
    # Assert the Report instance has the correct attributes
    assert report.id == 1
    assert report.report_name == "Test Report"
    assert report.report_type == "traffic_analysis"
    assert report.parameters == {"date_range": "last-30-days", "metrics": ["pageviews", "sessions"]}
    assert isinstance(report.create_time, datetime.datetime)
    assert report.create_time.year == 2023
    assert report.create_time.month == 1
    assert report.create_time.day == 1
    assert report.create_time.hour == 12
    assert report.status == "completed"
    assert report.file_path == "/path/to/report.pdf"


def test_report_update_status():
    """Test the update_status method."""
    # Setup a mock database object
    class MockDatabase:
        def execute(self, query, params=None, commit=False, fetchone=False, fetchall=False):
            # This is a very simple mock for the execute method
            cursor = type('cursor', (), {'lastrowid': 1})()
            return cursor
    
    mock_db = MockDatabase()
    
    # Create a Report instance with an ID
    report = Report(
        database=mock_db,
        report_name="Test Report",
        report_type="traffic_analysis",
        status="pending",
        id_val=1
    )
    
    # Update the status
    result = report.update_status("completed", "/path/to/report.pdf")
    
    # Assert the status and file_path were updated
    assert report.status == "completed"
    assert report.file_path == "/path/to/report.pdf"
    assert result is True  # update_status should return True if save succeeds


def test_report_repr():
    """Test the string representation of a Report instance."""
    # Setup a mock database object
    mock_db = object()
    
    # Create a Report instance
    create_time = datetime.datetime(2023, 1, 1, 12, 0, 0)
    report = Report(
        database=mock_db,
        report_name="Test Report",
        report_type="traffic_analysis",
        create_time=create_time,
        status="pending",
        id_val=1
    )
    
    # Get the string representation
    repr_str = repr(report)
    
    # Assert the string representation contains the essential attributes
    assert "Report" in repr_str
    assert "id=1" in repr_str
    assert "name='Test Report'" in repr_str
    assert "type='traffic_analysis'" in repr_str
    assert "status='pending'" in repr_str
    assert "created='2023-01-01 12:00'" in repr_str