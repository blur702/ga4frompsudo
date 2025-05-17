"""
Unit tests for the date_utils module.
Tests date parsing, formatting, and other date-related utility functions.
"""

import datetime
import pytest
from app.utils.date_utils import (
    parse_date_range,
    date_range_to_ga4_api_format,
    get_date_periods,
    format_date_for_display
)

class TestDateUtils:
    """Tests for the date_utils module."""

    def test_parse_date_range_today(self):
        """Test parsing 'today' date range."""
        today = datetime.date.today()
        expected = {
            'startDate': today.strftime('%Y-%m-%d'),
            'endDate': today.strftime('%Y-%m-%d')
        }
        result = parse_date_range('today')
        assert result == expected

    def test_parse_date_range_yesterday(self):
        """Test parsing 'yesterday' date range."""
        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        expected = {
            'startDate': yesterday.strftime('%Y-%m-%d'),
            'endDate': yesterday.strftime('%Y-%m-%d')
        }
        result = parse_date_range('yesterday')
        assert result == expected

    def test_parse_date_range_last_7_days(self):
        """Test parsing 'last-7-days' date range."""
        today = datetime.date.today()
        start_date = today - datetime.timedelta(days=6)  # Includes today as the 7th day
        expected = {
            'startDate': start_date.strftime('%Y-%m-%d'),
            'endDate': today.strftime('%Y-%m-%d')
        }
        result = parse_date_range('last-7-days')
        assert result == expected

    def test_parse_date_range_last_30_days(self):
        """Test parsing 'last-30-days' date range."""
        today = datetime.date.today()
        start_date = today - datetime.timedelta(days=29)
        expected = {
            'startDate': start_date.strftime('%Y-%m-%d'),
            'endDate': today.strftime('%Y-%m-%d')
        }
        result = parse_date_range('last-30-days')
        assert result == expected

    def test_parse_date_range_custom(self):
        """Test parsing custom date range."""
        expected = {
            'startDate': '2023-01-01',
            'endDate': '2023-01-31'
        }
        result = parse_date_range('2023-01-01,2023-01-31')
        assert result == expected

    def test_parse_date_range_invalid(self):
        """Test parsing invalid date range."""
        today = datetime.date.today()
        default_days = 30
        start_date = today - datetime.timedelta(days=default_days - 1)
        expected = {
            'startDate': start_date.strftime('%Y-%m-%d'),
            'endDate': today.strftime('%Y-%m-%d')
        }
        result = parse_date_range('invalid_range')
        assert result == expected

    def test_date_range_to_ga4_api_format_today(self):
        """Test converting today's date to GA4 API format."""
        today = datetime.date.today().strftime('%Y-%m-%d')
        result = date_range_to_ga4_api_format(today, today)
        assert result == {'startDate': 'today', 'endDate': 'today'}

    def test_date_range_to_ga4_api_format_yesterday(self):
        """Test converting yesterday's date to GA4 API format."""
        yesterday = (datetime.date.today() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        result = date_range_to_ga4_api_format(yesterday, yesterday)
        assert result == {'startDate': 'yesterday', 'endDate': 'yesterday'}

    def test_date_range_to_ga4_api_format_custom(self):
        """Test converting custom date range to GA4 API format."""
        start_date = '2023-01-01'
        end_date = '2023-01-31'
        result = date_range_to_ga4_api_format(start_date, end_date)
        assert result == {'startDate': start_date, 'endDate': end_date}

    def test_get_date_periods_days(self):
        """Test generating daily date periods."""
        result = get_date_periods('2023-01-01', '2023-01-03', 'day')
        expected = ['2023-01-01', '2023-01-02', '2023-01-03']
        assert result == expected

    def test_get_date_periods_weeks(self):
        """Test generating weekly date periods."""
        result = get_date_periods('2023-01-02', '2023-01-15', 'week')
        # First week starts Monday, Jan 2 and ends Sunday, Jan 8
        # Second week starts Monday, Jan 9 and ends Sunday, Jan 15
        expected = [
            ('2023-01-02', '2023-01-08'),
            ('2023-01-09', '2023-01-15')
        ]
        assert result == expected

    def test_get_date_periods_months(self):
        """Test generating monthly date periods."""
        result = get_date_periods('2023-01-15', '2023-02-15', 'month')
        expected = [
            ('2023-01-15', '2023-01-31'),
            ('2023-02-01', '2023-02-15')
        ]
        assert result == expected

    def test_get_date_periods_invalid_dates(self):
        """Test generating date periods with invalid dates."""
        result = get_date_periods('invalid', '2023-01-31', 'day')
        assert result == []

    def test_get_date_periods_start_after_end(self):
        """Test generating date periods with start date after end date."""
        result = get_date_periods('2023-01-31', '2023-01-01', 'day')
        assert result == []

    def test_format_date_for_display_date_object(self):
        """Test formatting date object for display."""
        date_obj = datetime.date(2023, 1, 15)
        result = format_date_for_display(date_obj)
        assert result == "January 15, 2023"

    def test_format_date_for_display_datetime_object(self):
        """Test formatting datetime object for display."""
        date_obj = datetime.datetime(2023, 1, 15, 12, 30, 45)
        result = format_date_for_display(date_obj)
        assert result == "January 15, 2023"

    def test_format_date_for_display_string(self):
        """Test formatting date string for display."""
        date_str = "2023-01-15"
        result = format_date_for_display(date_str)
        assert result == "January 15, 2023"

    def test_format_date_for_display_custom_format(self):
        """Test formatting date with custom format."""
        date_obj = datetime.date(2023, 1, 15)
        result = format_date_for_display(date_obj, "%d/%m/%Y")
        assert result == "15/01/2023"

    def test_format_date_for_display_invalid_string(self):
        """Test formatting invalid date string."""
        date_str = "invalid_date"
        result = format_date_for_display(date_str)
        assert result == "invalid_date"  # Should return original string if parsing fails