"""
Tests for the date utils module.
"""

import datetime
from app.utils.date_utils import (
    parse_date_range,
    date_range_to_ga4_api_format,
    get_date_periods,
    format_date_for_display
)


def test_parse_date_range_today():
    """Test parsing 'today' date range."""
    today = datetime.date.today()
    today_str = today.strftime('%Y-%m-%d')
    
    result = parse_date_range('today')
    
    assert result['startDate'] == today_str
    assert result['endDate'] == today_str


def test_parse_date_range_yesterday():
    """Test parsing 'yesterday' date range."""
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    yesterday_str = yesterday.strftime('%Y-%m-%d')
    
    result = parse_date_range('yesterday')
    
    assert result['startDate'] == yesterday_str
    assert result['endDate'] == yesterday_str


def test_parse_date_range_last_7_days():
    """Test parsing 'last-7-days' date range."""
    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=6)
    
    result = parse_date_range('last-7-days')
    
    assert result['startDate'] == start_date.strftime('%Y-%m-%d')
    assert result['endDate'] == today.strftime('%Y-%m-%d')


def test_parse_date_range_last_30_days():
    """Test parsing 'last-30-days' date range."""
    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=29)
    
    result = parse_date_range('last-30-days')
    
    assert result['startDate'] == start_date.strftime('%Y-%m-%d')
    assert result['endDate'] == today.strftime('%Y-%m-%d')


def test_parse_date_range_last_90_days():
    """Test parsing 'last-90-days' date range."""
    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=89)
    
    result = parse_date_range('last-90-days')
    
    assert result['startDate'] == start_date.strftime('%Y-%m-%d')
    assert result['endDate'] == today.strftime('%Y-%m-%d')


def test_parse_date_range_custom():
    """Test parsing custom date range in format 'YYYY-MM-DD,YYYY-MM-DD'."""
    result = parse_date_range('2023-01-01,2023-01-31')
    
    assert result['startDate'] == '2023-01-01'
    assert result['endDate'] == '2023-01-31'


def test_parse_date_range_custom_swapped():
    """Test parsing custom date range with end date before start date (should swap them)."""
    result = parse_date_range('2023-01-31,2023-01-01')
    
    # Dates should be swapped to ensure start_date <= end_date
    assert result['startDate'] == '2023-01-01'
    assert result['endDate'] == '2023-01-31'


def test_parse_date_range_invalid_custom():
    """Test parsing invalid custom date range."""
    today = datetime.date.today()
    default_start = today - datetime.timedelta(days=29)  # 30 days ago (inclusive of today)
    
    result = parse_date_range('invalid-format')
    
    # Should fall back to default 30 days
    assert result['startDate'] == default_start.strftime('%Y-%m-%d')
    assert result['endDate'] == today.strftime('%Y-%m-%d')


def test_date_range_to_ga4_api_format_normal_dates():
    """Test conversion of normal date strings to GA4 API format."""
    result = date_range_to_ga4_api_format('2023-01-01', '2023-01-31')
    
    # Should keep the same format for dates that aren't special keywords
    assert result['startDate'] == '2023-01-01'
    assert result['endDate'] == '2023-01-31'


def test_date_range_to_ga4_api_format_today():
    """Test conversion of today's date to GA4 API format."""
    today = datetime.date.today().strftime('%Y-%m-%d')
    
    result = date_range_to_ga4_api_format(today, today)
    
    # Should convert to 'today' keyword
    assert result['startDate'] == 'today'
    assert result['endDate'] == 'today'


def test_date_range_to_ga4_api_format_yesterday():
    """Test conversion of yesterday's date to GA4 API format."""
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    
    result = date_range_to_ga4_api_format(yesterday, yesterday)
    
    # Should convert to 'yesterday' keyword
    assert result['startDate'] == 'yesterday'
    assert result['endDate'] == 'yesterday'


def test_date_range_to_ga4_api_format_mixed():
    """Test conversion with today and a regular date."""
    today = datetime.date.today().strftime('%Y-%m-%d')
    
    result = date_range_to_ga4_api_format('2023-01-01', today)
    
    # Start date should remain as is, end date should be 'today'
    assert result['startDate'] == '2023-01-01'
    assert result['endDate'] == 'today'


def test_get_date_periods_day():
    """Test generating daily periods between dates."""
    result = get_date_periods('2023-01-01', '2023-01-03', 'day')
    
    # Should return a list of 3 dates
    assert len(result) == 3
    assert result[0] == '2023-01-01'
    assert result[1] == '2023-01-02'
    assert result[2] == '2023-01-03'


def test_get_date_periods_week():
    """Test generating weekly periods between dates."""
    # This spans two weeks
    result = get_date_periods('2023-01-02', '2023-01-15', 'week')
    
    # Should return a list of tuples, each representing a week
    assert len(result) > 0
    # Check that each item is a tuple with start and end dates
    for period in result:
        assert isinstance(period, tuple)
        assert len(period) == 2
        start, end = period
        assert isinstance(start, str)
        assert isinstance(end, str)


def test_get_date_periods_month():
    """Test generating monthly periods between dates."""
    # This spans two months
    result = get_date_periods('2023-01-15', '2023-02-15', 'month')
    
    # Should return a list of tuples, each representing a month
    assert len(result) == 2
    # Check structure of first month (partial)
    assert isinstance(result[0], tuple)
    start1, end1 = result[0]
    assert start1 == '2023-01-15'
    assert end1 == '2023-01-31'
    
    # Check structure of second month (partial)
    assert isinstance(result[1], tuple)
    start2, end2 = result[1]
    assert start2 == '2023-02-01'
    assert end2 == '2023-02-15'


def test_get_date_periods_invalid_dates():
    """Test generating periods with invalid date strings."""
    result = get_date_periods('invalid', '2023-01-03', 'day')
    
    # Should return empty list for invalid dates
    assert result == []


def test_get_date_periods_start_after_end():
    """Test generating periods with start date after end date."""
    result = get_date_periods('2023-01-03', '2023-01-01', 'day')
    
    # Should return empty list when start date is after end date
    assert result == []


def test_get_date_periods_unsupported_period():
    """Test generating periods with unsupported period type."""
    result = get_date_periods('2023-01-01', '2023-01-03', 'unsupported')
    
    # Should return empty list for unsupported period type
    assert result == []


def test_format_date_for_display_datetime():
    """Test formatting a datetime object for display."""
    dt = datetime.datetime(2023, 5, 15, 12, 30, 45)
    
    result = format_date_for_display(dt)
    
    # Default format is "%B %d, %Y"
    assert result == "May 15, 2023"


def test_format_date_for_display_date_str():
    """Test formatting a date string for display."""
    date_str = "2023-05-15"
    
    result = format_date_for_display(date_str)
    
    assert result == "May 15, 2023"


def test_format_date_for_display_datetime_str():
    """Test formatting a datetime string for display."""
    datetime_str = "2023-05-15T12:30:45"
    
    result = format_date_for_display(datetime_str)
    
    assert result == "May 15, 2023"


def test_format_date_for_display_custom_format():
    """Test formatting a date with a custom format string."""
    dt = datetime.datetime(2023, 5, 15, 12, 30, 45)
    
    result = format_date_for_display(dt, output_format="%Y/%m/%d")
    
    assert result == "2023/05/15"


def test_format_date_for_display_invalid_date_str():
    """Test formatting an invalid date string."""
    invalid_date = "not-a-date"
    
    result = format_date_for_display(invalid_date)
    
    # Should return the original string if parsing fails
    assert result == invalid_date