import os
import unittest
from unittest.mock import patch, MagicMock

from flask import Flask

from app.services.ga4_service import GA4Service


class TestGA4Service(unittest.TestCase):
    """Test suite for the GA4Service class."""

    def setUp(self):
        """Set up the test environment before each test."""
        # Create a test Flask app
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.app.config['GA4_CREDENTIALS_PATH'] = 'test-credentials.json'
        
        # Set up patches
        self.credentials_patch = patch('app.services.ga4_service.Credentials')
        self.analytics_patch = patch('app.services.ga4_service.build')
        
        # Start the patches
        self.mock_credentials = self.credentials_patch.start()
        self.mock_build = self.analytics_patch.start()
        
        # Mock credentials and API clients
        self.mock_credentials.from_service_account_file.return_value = MagicMock()
        self.mock_analytics = MagicMock()
        self.mock_data = MagicMock()
        self.mock_admin = MagicMock()
        
        # Configure mock build function
        def mock_build_func(service_name, version, credentials):
            if service_name == 'analyticsadmin':
                return self.mock_analytics
            elif service_name == 'analyticsdata':
                return self.mock_data
            return MagicMock()
            
        self.mock_build.side_effect = mock_build_func
        
        # Mock API responses
        self.mock_analytics.accountSummaries.return_value = self.mock_admin
        
        # Create the GA4 service
        with patch('os.path.exists', return_value=True):
            with self.app.app_context():
                self.ga4_service = GA4Service('test-credentials.json')

    def tearDown(self):
        """Clean up resources after each test."""
        # Stop all patches
        self.credentials_patch.stop()
        self.analytics_patch.stop()

    def test_initialization(self):
        """Test service initialization with credentials."""
        self.assertTrue(self.ga4_service.is_available())
        self.mock_credentials.from_service_account_file.assert_called_once()
        self.mock_build.assert_any_call('analyticsadmin', 'v1beta', credentials=self.mock_credentials.from_service_account_file.return_value)
        self.mock_build.assert_any_call('analyticsdata', 'v1beta', credentials=self.mock_credentials.from_service_account_file.return_value)

    def test_initialization_without_credentials(self):
        """Test service initialization without credentials."""
        with patch('os.path.exists', return_value=False):
            with self.app.app_context():
                service = GA4Service('non-existent-credentials.json')
                self.assertFalse(service.is_available())

    def test_list_account_summaries(self):
        """Test listing account summaries."""
        # Configure mock response
        mock_response = {
            'accountSummaries': [
                {'name': 'accounts/123', 'displayName': 'Test Account'},
                {'name': 'accounts/456', 'displayName': 'Another Account'}
            ]
        }
        self.mock_admin.list().execute.return_value = mock_response
        
        # Call the method
        result = self.ga4_service.list_account_summaries()
        
        # Assertions
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['name'], 'accounts/123')
        self.assertEqual(result[1]['displayName'], 'Another Account')
        self.mock_admin.list.assert_called_once()

    def test_list_properties(self):
        """Test listing properties."""
        # Configure mock response
        mock_account_summaries = {
            'accountSummaries': [
                {
                    'name': 'accounts/123',
                    'propertySummaries': [
                        {'name': 'properties/UA-123-1', 'displayName': 'Website 1'},
                        {'name': 'properties/UA-123-2', 'displayName': 'Website 2'}
                    ]
                },
                {
                    'name': 'accounts/456',
                    'propertySummaries': [
                        {'name': 'properties/UA-456-1', 'displayName': 'Website 3'}
                    ]
                }
            ]
        }
        self.mock_admin.list().execute.return_value = mock_account_summaries
        
        # Call the method
        result = self.ga4_service.list_properties()
        
        # Assertions
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]['name'], 'properties/UA-123-1')
        self.assertEqual(result[1]['displayName'], 'Website 2')
        self.assertEqual(result[2]['name'], 'properties/UA-456-1')

    def test_list_properties_with_account_filter(self):
        """Test listing properties filtered by account ID."""
        # Configure mock response
        mock_account_summaries = {
            'accountSummaries': [
                {
                    'account': 'accounts/123',
                    'propertySummaries': [
                        {'name': 'properties/UA-123-1', 'displayName': 'Website 1'},
                        {'name': 'properties/UA-123-2', 'displayName': 'Website 2'}
                    ]
                },
                {
                    'account': 'accounts/456',
                    'propertySummaries': [
                        {'name': 'properties/UA-456-1', 'displayName': 'Website 3'}
                    ]
                }
            ]
        }
        self.mock_admin.list().execute.return_value = mock_account_summaries
        
        # Call the method
        result = self.ga4_service.list_properties(account_id='123')
        
        # Assertions
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['name'], 'properties/UA-123-1')
        self.assertEqual(result[1]['displayName'], 'Website 2')

    def test_get_property(self):
        """Test getting a specific property."""
        # Configure mock response
        mock_property = {
            'name': 'properties/UA-123-1',
            'displayName': 'Website 1',
            'createTime': '2022-01-01T00:00:00Z'
        }
        self.mock_analytics.properties().get().execute.return_value = mock_property
        
        # Call the method
        result = self.ga4_service.get_property('UA-123-1')
        
        # Assertions
        self.assertEqual(result['name'], 'properties/UA-123-1')
        self.assertEqual(result['displayName'], 'Website 1')
        self.mock_analytics.properties().get.assert_called_with(name='properties/UA-123-1')

    def test_list_streams(self):
        """Test listing data streams for a property."""
        # Configure mock response
        mock_streams = {
            'dataStreams': [
                {'name': 'properties/UA-123-1/dataStreams/123', 'displayName': 'Web Stream'},
                {'name': 'properties/UA-123-1/dataStreams/456', 'displayName': 'App Stream'}
            ]
        }
        self.mock_analytics.properties().dataStreams().list().execute.return_value = mock_streams
        
        # Call the method
        result = self.ga4_service.list_streams('UA-123-1')
        
        # Assertions
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['name'], 'properties/UA-123-1/dataStreams/123')
        self.assertEqual(result[1]['displayName'], 'App Stream')
        self.mock_analytics.properties().dataStreams().list.assert_called_with(parent='properties/UA-123-1')

    def test_run_report(self):
        """Test running a basic GA4 report."""
        # Configure mock response
        mock_report_response = {
            'rows': [
                {
                    'dimensionValues': [{'value': '2022-01-01'}],
                    'metricValues': [{'value': '100'}, {'value': '50'}]
                },
                {
                    'dimensionValues': [{'value': '2022-01-02'}],
                    'metricValues': [{'value': '120'}, {'value': '60'}]
                }
            ],
            'dimensionHeaders': [{'name': 'date'}],
            'metricHeaders': [{'name': 'sessions'}, {'name': 'users'}]
        }
        self.mock_data.properties().runReport().execute.return_value = mock_report_response
        
        # Call the method
        result = self.ga4_service.run_report(
            property_id='UA-123-1',
            start_date='2022-01-01',
            end_date='2022-01-31',
            metrics=['sessions', 'users'],
            dimensions=['date']
        )
        
        # Assertions
        self.assertEqual(len(result['rows']), 2)
        self.mock_data.properties().runReport.assert_called_once()
        # Verify the request payload
        args, kwargs = self.mock_data.properties().runReport.call_args
        self.assertEqual(kwargs['property'], 'properties/UA-123-1')
        self.assertEqual(kwargs['body']['metrics'], [{'name': 'sessions'}, {'name': 'users'}])
        self.assertEqual(kwargs['body']['dimensions'], [{'name': 'date'}])

    def test_get_traffic_report(self):
        """Test getting a traffic analysis report."""
        # Configure the mock
        self.ga4_service.run_report = MagicMock()
        mock_report = {'rows': [{'data': 'test'}]}
        self.ga4_service.run_report.return_value = mock_report
        
        # Call the method
        result = self.ga4_service.get_traffic_report('UA-123-1', 'last7days')
        
        # Assertions
        self.assertEqual(result, mock_report)
        # Verify the right metrics and dimensions were used
        args, kwargs = self.ga4_service.run_report.call_args
        self.assertEqual(kwargs['property_id'], 'UA-123-1')
        self.assertEqual(set(kwargs['metrics']), {
            'totalUsers', 'newUsers', 'sessions', 'screenPageViews', 'averageSessionDuration'
        })
        self.assertEqual(kwargs['dimensions'], ['date'])

    def test_format_report_data(self):
        """Test formatting report data."""
        # Mock report data
        mock_report = {
            'rows': [
                {
                    'dimensionValues': [{'value': '2022-01-01'}],
                    'metricValues': [{'value': '100'}, {'value': '50'}]
                },
                {
                    'dimensionValues': [{'value': '2022-01-02'}],
                    'metricValues': [{'value': '120'}, {'value': '60'}]
                }
            ],
            'dimensionHeaders': [{'name': 'date'}],
            'metricHeaders': [{'name': 'sessions'}, {'name': 'users'}]
        }
        
        # Call the method
        result = self.ga4_service.format_report_data(mock_report)
        
        # Assertions
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['date'], '2022-01-01')
        self.assertEqual(result[0]['sessions'], '100')
        self.assertEqual(result[0]['users'], '50')
        self.assertEqual(result[1]['date'], '2022-01-02')
        self.assertEqual(result[1]['sessions'], '120')
        self.assertEqual(result[1]['users'], '60')

    def test_get_realtime_users(self):
        """Test getting realtime users count."""
        # Configure mock response
        mock_realtime_response = {
            'rows': [
                {'metricValues': [{'value': '42'}]}
            ],
            'metricHeaders': [{'name': 'activeUsers'}]
        }
        self.mock_data.properties().runRealtimeReport().execute.return_value = mock_realtime_response
        
        # Call the method
        result = self.ga4_service.get_realtime_users('UA-123-1')
        
        # Assertions
        self.assertEqual(result, 42)
        self.mock_data.properties().runRealtimeReport.assert_called_once()
        args, kwargs = self.mock_data.properties().runRealtimeReport.call_args
        self.assertEqual(kwargs['property'], 'properties/UA-123-1')
        self.assertEqual(kwargs['body']['metrics'], [{'name': 'activeUsers'}])


if __name__ == '__main__':
    unittest.main()