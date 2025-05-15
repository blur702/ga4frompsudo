import unittest
import datetime
from app.utils.formatters import (
    format_number, format_percentage, format_date, format_duration,
    format_file_size, format_metric_name, data_to_csv, data_to_json,
    format_dimension_value, format_ga4_report_data
)

class TestFormatters(unittest.TestCase):
    """Test suite for the formatter utilities."""

    def test_format_number(self):
        """Test number formatting."""
        # Basic formatting
        self.assertEqual(format_number(1234), "1,234")
        self.assertEqual(format_number(1234.56, precision=2), "1,234.56")
        
        # Test abbreviation
        self.assertEqual(format_number(1234, abbreviate=True), "1.2K")
        self.assertEqual(format_number(1234567, abbreviate=True), "1.2M")
        self.assertEqual(format_number(1234567890, abbreviate=True), "1.2B")
        
        # Test string input
        self.assertEqual(format_number("1234"), "1,234")
        
        # Test invalid input
        self.assertEqual(format_number("abc"), "abc")

    def test_format_percentage(self):
        """Test percentage formatting."""
        # Decimal input (0-1)
        self.assertEqual(format_percentage(0.75), "75.00%")
        self.assertEqual(format_percentage(0.75, precision=0), "75%")
        
        # Percentage input (>1)
        self.assertEqual(format_percentage(75), "75.00%")
        
        # No percentage sign
        self.assertEqual(format_percentage(0.75, include_sign=False), "75.00")
        
        # String input
        self.assertEqual(format_percentage("0.5"), "50.00%")
        
        # Invalid input
        self.assertEqual(format_percentage("abc"), "abc")

    def test_format_date(self):
        """Test date formatting."""
        # Test with date object
        date_obj = datetime.date(2023, 9, 15)
        self.assertEqual(format_date(date_obj), "2023-09-15")
        self.assertEqual(format_date(date_obj, format_str="%B %d, %Y"), "September 15, 2023")
        
        # Test with datetime object
        datetime_obj = datetime.datetime(2023, 9, 15, 14, 30, 0)
        self.assertEqual(format_date(datetime_obj), "2023-09-15")
        self.assertEqual(format_date(datetime_obj, format_str="%Y-%m-%d %H:%M"), "2023-09-15 14:30")
        
        # Test with string (YYYY-MM-DD)
        self.assertEqual(format_date("2023-09-15", format_str="%d/%m/%Y"), "15/09/2023")
        
        # Test with string (YYYYMMDD)
        self.assertEqual(format_date("20230915", format_str="%d/%m/%Y"), "15/09/2023")
        
        # Test with invalid string
        self.assertEqual(format_date("invalid date"), "invalid date")

    def test_format_duration(self):
        """Test duration formatting."""
        # Human-readable format
        self.assertEqual(format_duration(3665), "1h 1m 5s")
        self.assertEqual(format_duration(65), "1m 5s")
        self.assertEqual(format_duration(5), "5s")
        
        # Clock format
        self.assertEqual(format_duration(3665, format_type='clock'), "01:01:05")
        self.assertEqual(format_duration(65, format_type='clock'), "00:01:05")
        
        # Compact format
        self.assertEqual(format_duration(3665, format_type='compact'), "1h1m5s")
        self.assertEqual(format_duration(65, format_type='compact'), "1m5s")
        
        # String input
        self.assertEqual(format_duration("3665"), "1h 1m 5s")
        
        # Invalid input
        self.assertEqual(format_duration("abc"), "abc")

    def test_format_file_size(self):
        """Test file size formatting."""
        self.assertEqual(format_file_size(1024), "1.00 KB")
        self.assertEqual(format_file_size(1024 * 1024), "1.00 MB")
        self.assertEqual(format_file_size(1024 * 1024 * 1024), "1.00 GB")
        
        # Different precision
        self.assertEqual(format_file_size(1536, precision=1), "1.5 KB")
        
        # String input
        self.assertEqual(format_file_size("1024"), "1.00 KB")
        
        # Invalid input
        self.assertEqual(format_file_size("abc"), "abc")
        
        # Zero bytes
        self.assertEqual(format_file_size(0), "0 B")

    def test_format_metric_name(self):
        """Test metric name formatting."""
        # camelCase
        self.assertEqual(format_metric_name("screenPageViews"), "Screen Page Views")
        self.assertEqual(format_metric_name("totalUsers"), "Total Users")
        
        # snake_case
        self.assertEqual(format_metric_name("avg_session_duration"), "Avg Session Duration")
        self.assertEqual(format_metric_name("bounce_rate"), "Bounce Rate")

    def test_data_to_csv(self):
        """Test CSV conversion."""
        data = [
            {'name': 'John', 'age': 30},
            {'name': 'Alice', 'age': 25}
        ]
        
        # With headers
        expected_csv = "name,age\r\nJohn,30\r\nAlice,25\r\n"
        self.assertEqual(data_to_csv(data), expected_csv)
        
        # Without headers
        expected_csv_no_headers = "John,30\r\nAlice,25\r\n"
        self.assertEqual(data_to_csv(data, include_headers=False), expected_csv_no_headers)
        
        # Empty data
        self.assertEqual(data_to_csv([]), "")

    def test_data_to_json(self):
        """Test JSON conversion."""
        data = {'name': 'John', 'age': 30}
        
        # Compact format
        self.assertEqual(data_to_json(data), '{"name": "John", "age": 30}')
        
        # Pretty format
        expected_json = '{\n  "name": "John",\n  "age": 30\n}'
        self.assertEqual(data_to_json(data, pretty=True), expected_json)

    def test_format_dimension_value(self):
        """Test dimension value formatting."""
        # Date dimension
        self.assertTrue(',' in format_dimension_value('date', '20230915'))  # Should format as date
        
        # Device category
        self.assertEqual(format_dimension_value('deviceCategory', 'mobile'), 'Mobile')
        
        # Page path truncation
        long_path = '/this/is/a/very/long/path/that/should/be/truncated/because/it/exceeds/fifty/characters'
        self.assertTrue(len(format_dimension_value('pagePath', long_path)) < len(long_path))
        self.assertTrue(format_dimension_value('pagePath', long_path).endswith('...'))
        
        # Other dimensions
        self.assertEqual(format_dimension_value('country', 'United States'), 'United States')

    def test_format_ga4_report_data(self):
        """Test GA4 report data formatting."""
        # Mock GA4 report data
        report_data = {
            'dimensionHeaders': [{'name': 'date'}, {'name': 'deviceCategory'}],
            'metricHeaders': [{'name': 'screenPageViews'}, {'name': 'bounceRate'}, {'name': 'averageSessionDuration'}],
            'rows': [
                {
                    'dimensionValues': [{'value': '20230915'}, {'value': 'mobile'}],
                    'metricValues': [{'value': '1234'}, {'value': '0.55'}, {'value': '120'}]
                },
                {
                    'dimensionValues': [{'value': '20230916'}, {'value': 'desktop'}],
                    'metricValues': [{'value': '5678'}, {'value': '0.45'}, {'value': '180'}]
                }
            ]
        }
        
        formatted_data = format_ga4_report_data(report_data)
        
        # Check length
        self.assertEqual(len(formatted_data), 2)
        
        # Check dimension formatting
        self.assertTrue(',' in formatted_data[0]['date'])  # Date should be formatted
        self.assertEqual(formatted_data[0]['deviceCategory'], 'Mobile')  # Should be capitalized
        
        # Check metric formatting
        self.assertEqual(formatted_data[0]['screenPageViews'], '1,234')  # Should have comma
        self.assertEqual(formatted_data[0]['bounceRate'], '55.00%')  # Should be formatted as percentage
        self.assertEqual(formatted_data[0]['averageSessionDuration'], '2m 0s')  # Should be formatted as duration


if __name__ == '__main__':
    unittest.main()