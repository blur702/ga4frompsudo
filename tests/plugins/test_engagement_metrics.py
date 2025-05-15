import unittest
from unittest.mock import patch, MagicMock

from app.plugins.engagement_metrics import EngagementMetricsPlugin


class TestEngagementMetricsPlugin(unittest.TestCase):
    """Test suite for the EngagementMetricsPlugin."""

    def setUp(self):
        """Set up the test environment before each test."""
        self.plugin = EngagementMetricsPlugin()
        
        # Create sample GA4 data
        self.sample_data = [
            {
                'date': '20220101',
                'engagementRate': '0.65',
                'averageSessionDuration': '120.5',
                'bounceRate': '0.35',
                'screenPageViewsPerSession': '3.2'
            },
            {
                'date': '20220102',
                'engagementRate': '0.68',
                'averageSessionDuration': '130.2',
                'bounceRate': '0.32',
                'screenPageViewsPerSession': '3.5'
            },
            {
                'date': '20220103',
                'engagementRate': '0.72',
                'averageSessionDuration': '145.8',
                'bounceRate': '0.28',
                'screenPageViewsPerSession': '3.8'
            }
        ]

    def test_plugin_initialization(self):
        """Test that the plugin initializes correctly with proper metadata."""
        self.assertEqual(self.plugin.PLUGIN_ID, "engagement_metrics")
        self.assertEqual(self.plugin.PLUGIN_NAME, "Engagement Metrics")
        self.assertEqual(self.plugin.PLUGIN_CATEGORY, "Analytics")
        
        # Test plugin info method
        info = self.plugin.get_info()
        self.assertEqual(info['id'], "engagement_metrics")
        self.assertEqual(info['name'], "Engagement Metrics")
        self.assertIn('version', info)
        self.assertIn('description', info)

    def test_default_config(self):
        """Test that the plugin provides appropriate default configuration."""
        config = self.plugin.get_default_config()
        
        self.assertIn('metrics', config)
        self.assertIn('dimensions', config)
        self.assertIn('time_period', config)
        self.assertIn('chart_type', config)
        
        self.assertIn('engagementRate', config['metrics'])
        self.assertIn('date', config['dimensions'])
        self.assertEqual(config['time_period'], 'last30days')
        self.assertEqual(config['chart_type'], 'line')

    def test_config_validation(self):
        """Test that the configuration validation works correctly."""
        # Valid config
        valid_config = {
            'metrics': ['engagementRate', 'bounceRate'],
            'dimensions': ['date'],
            'time_period': 'last30days',
            'chart_type': 'line'
        }
        
        errors = self.plugin.validate_config(valid_config)
        self.assertEqual(len(errors), 0)
        
        # Invalid config - missing metrics
        invalid_config = {
            'metrics': [],
            'dimensions': ['date'],
            'time_period': 'last30days',
            'chart_type': 'line'
        }
        
        errors = self.plugin.validate_config(invalid_config)
        self.assertGreater(len(errors), 0)
        
        # Invalid config - invalid time period
        invalid_config = {
            'metrics': ['engagementRate'],
            'dimensions': ['date'],
            'time_period': 'invalid_period',
            'chart_type': 'line'
        }
        
        errors = self.plugin.validate_config(invalid_config)
        self.assertGreater(len(errors), 0)

    def test_calculate_additional_metrics(self):
        """Test the calculation of additional metrics from raw data."""
        result = self.plugin._calculate_additional_metrics(self.sample_data)
        
        self.assertIn('raw_data', result)
        self.assertIn('summary', result)
        self.assertIn('trends', result)
        
        # Check summary calculations
        summary = result['summary']
        self.assertIn('avg_engagementRate', summary)
        self.assertAlmostEqual(summary['avg_engagementRate'], 0.68333, places=4)
        
        self.assertIn('min_bounceRate', summary)
        self.assertEqual(summary['min_bounceRate'], 0.28)
        
        self.assertIn('max_averageSessionDuration', summary)
        self.assertEqual(summary['max_averageSessionDuration'], 145.8)
        
        # Check trend calculations
        trends = result['trends']
        self.assertIn('engagementRate', trends)
        self.assertEqual(trends['engagementRate']['first_value'], 0.65)
        self.assertEqual(trends['engagementRate']['last_value'], 0.72)
        self.assertAlmostEqual(trends['engagementRate']['percent_change'], 10.769, places=3)
        self.assertEqual(trends['engagementRate']['direction'], 'up')
        
        self.assertIn('bounceRate', trends)
        self.assertEqual(trends['bounceRate']['direction'], 'down')

    @patch('app.services.get_service')
    def test_process_data(self, mock_get_service):
        """Test the main data processing functionality."""
        # Mock GA4 service
        mock_ga4_service = MagicMock()
        mock_ga4_service.is_available.return_value = True
        mock_ga4_service.run_report.return_value = {"rows": self.sample_data}
        mock_ga4_service.format_report_data.return_value = self.sample_data
        mock_ga4_service._format_datetime_for_display.return_value = "2022-01-04 12:00:00"
        
        # Set up the mock service
        mock_get_service.return_value = mock_ga4_service
        
        # Test data processing
        input_data = {
            'property_id': 'UA-123456-1',
            'date_range': 'last7days'
        }
        
        result = self.plugin.process_data(input_data)
        
        # Verify correct methods were called
        mock_get_service.assert_called_once_with('ga4')
        mock_ga4_service.is_available.assert_called_once()
        mock_ga4_service.run_report.assert_called_once()
        mock_ga4_service.format_report_data.assert_called_once()
        
        # Check result structure
        self.assertIn('raw_data', result)
        self.assertIn('summary', result)
        self.assertIn('trends', result)
        self.assertIn('visualizations', result)
        self.assertIn('metadata', result)
        
        # Check metadata
        metadata = result['metadata']
        self.assertEqual(metadata['property_id'], 'UA-123456-1')
        self.assertEqual(metadata['date_range'], 'last7days')
        
        # Check visualizations
        visualizations = result['visualizations']
        self.assertIn('primary_chart', visualizations)
        self.assertEqual(visualizations['primary_chart']['type'], 'line')
        self.assertGreater(len(visualizations['primary_chart']['series']), 0)

    @patch('app.services.get_service')
    def test_process_data_error_handling(self, mock_get_service):
        """Test error handling in the data processing."""
        # Test with GA4 service not available
        mock_get_service.return_value = None
        
        result = self.plugin.process_data({'property_id': 'UA-123456-1'})
        self.assertIn('error', result)
        self.assertEqual(result['error'], 'GA4 service not available')
        
        # Test with exception during processing
        mock_ga4_service = MagicMock()
        mock_ga4_service.is_available.return_value = True
        mock_ga4_service.run_report.side_effect = Exception("Test error")
        mock_get_service.return_value = mock_ga4_service
        
        result = self.plugin.process_data({'property_id': 'UA-123456-1'})
        self.assertIn('error', result)
        self.assertIn('Failed to process engagement metrics', result['error'])

    def test_empty_data_handling(self):
        """Test handling of empty data sets."""
        result = self.plugin._calculate_additional_metrics([])
        
        self.assertIn('raw_data', result)
        self.assertIn('summary', result)
        self.assertIn('trends', result)
        
        self.assertEqual(len(result['raw_data']), 0)
        self.assertEqual(len(result['summary']), 0)
        self.assertEqual(len(result['trends']), 0)

    def test_permissions_and_assets(self):
        """Test that the plugin correctly reports its permissions and assets."""
        # Check permissions
        permissions = self.plugin.get_required_permissions()
        self.assertIn('ga4:read', permissions)
        
        # Check templates
        templates = self.plugin.get_templates()
        self.assertGreater(len(templates), 0)
        self.assertIn('engagement_dashboard', templates)
        
        # Check scripts
        scripts = self.plugin.get_scripts()
        self.assertGreater(len(scripts), 0)
        self.assertTrue(any('charts.js' in script for script in scripts))
        
        # Check styles
        styles = self.plugin.get_styles()
        self.assertGreater(len(styles), 0)
        self.assertTrue(any('engagement.css' in style for style in styles))


if __name__ == '__main__':
    unittest.main()