import os
import unittest
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock

from flask import Flask

from app.services.report_service import ReportService
from app.models.report import Report
from app.models.report_data import ReportData


class TestReportService(unittest.TestCase):
    """Test suite for the ReportService class."""
    
    def setUp(self):
        """Set up the test environment before each test."""
        # Create a test Flask app
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        
        # Create a temporary directory for report outputs
        self.temp_dir = tempfile.mkdtemp()
        self.app.config['REPORTS_DIR'] = self.temp_dir
        
        # Create the report service
        with self.app.app_context():
            self.report_service = ReportService()
    
    def tearDown(self):
        """Clean up resources after each test."""
        # Remove the temporary directory
        shutil.rmtree(self.temp_dir)
    
    @patch('app.models.report.Report.save')
    def test_create_report(self, mock_save):
        """Test creating a new report."""
        # Configure mock
        mock_save.return_value = 123
        
        with self.app.app_context():
            # Call the method
            report_id = self.report_service.create_report(
                report_name="Test Report",
                report_type="test",
                parameters={"test_param": "value"}
            )
            
            # Assertions
            self.assertEqual(report_id, 123)
            mock_save.assert_called_once()
    
    @patch('app.models.report.Report.find_by_id')
    @patch('app.services.get_service')
    def test_generate_report_success(self, mock_get_service, mock_find_by_id):
        """Test successful report generation."""
        # Configure mocks
        mock_report = MagicMock(spec=Report)
        mock_report.id = 123
        mock_report.report_name = "Test Report"
        mock_report.report_type = "test"
        mock_report.parameters = json.dumps({"test_param": "value"})
        mock_report.status = "pending"
        mock_find_by_id.return_value = mock_report
        
        # Mock plugin service and plugin
        mock_plugin_service = MagicMock()
        mock_plugin = MagicMock()
        mock_plugin.process_data.return_value = {
            "raw_data": [
                {"date": "20220101", "metric1": "100", "metric2": "200"}
            ],
            "summary": {"avg_metric1": 100, "avg_metric2": 200},
            "trends": {"metric1": {"direction": "up", "percent_change": 10}}
        }
        mock_plugin_service.get_plugin_instance.return_value = mock_plugin
        
        # Mock GA4 service
        mock_ga4_service = MagicMock()
        mock_ga4_service.is_available.return_value = True
        
        # Set up get_service to return our mock services
        def mock_service_getter(service_name):
            if service_name == 'plugin':
                return mock_plugin_service
            elif service_name == 'ga4':
                return mock_ga4_service
            return None
            
        mock_get_service.side_effect = mock_service_getter
        
        with self.app.app_context():
            # Patch the _generate_json_report method to return a predictable path
            with patch.object(self.report_service, '_generate_json_report', return_value=os.path.join(self.temp_dir, 'test_report.json')):
                # Call the method
                result = self.report_service.generate_report(123, format_type='json')
                
                # Assertions
                self.assertIsNotNone(result)
                self.assertTrue('test_report.json' in result)
                
                # Verify the mocks were called correctly
                mock_find_by_id.assert_called_once_with(123)
                mock_plugin_service.get_plugin_instance.assert_called_once()
                mock_plugin.process_data.assert_called_once()
                mock_report.save.assert_called()  # Should be called to update status
    
    @patch('app.models.report.Report.find_by_id')
    def test_generate_report_report_not_found(self, mock_find_by_id):
        """Test report generation when report is not found."""
        # Configure mock to return None (report not found)
        mock_find_by_id.return_value = None
        
        with self.app.app_context():
            # Call the method
            result = self.report_service.generate_report(999)
            
            # Assertions
            self.assertIsNone(result)
            mock_find_by_id.assert_called_once_with(999)
    
    @patch('app.models.report.Report.find_by_id')
    @patch('app.services.get_service')
    def test_generate_report_plugin_not_found(self, mock_get_service, mock_find_by_id):
        """Test report generation when plugin is not found."""
        # Configure report mock
        mock_report = MagicMock(spec=Report)
        mock_report.id = 123
        mock_report.report_name = "Test Report"
        mock_report.report_type = "test"
        mock_report.parameters = json.dumps({"plugin_id": "nonexistent_plugin"})
        mock_report.status = "pending"
        mock_find_by_id.return_value = mock_report
        
        # Mock plugin service to return None for plugin
        mock_plugin_service = MagicMock()
        mock_plugin_service.get_plugin_instance.return_value = None
        
        # Mock GA4 service
        mock_ga4_service = MagicMock()
        mock_ga4_service.is_available.return_value = True
        
        # Set up get_service
        def mock_service_getter(service_name):
            if service_name == 'plugin':
                return mock_plugin_service
            elif service_name == 'ga4':
                return mock_ga4_service
            return None
            
        mock_get_service.side_effect = mock_service_getter
        
        with self.app.app_context():
            # Call the method
            result = self.report_service.generate_report(123)
            
            # Assertions
            self.assertIsNone(result)
            mock_plugin_service.get_plugin_instance.assert_called_once()
            self.assertEqual(mock_report.status, "failed")
    
    @patch('app.models.report.Report.find_by_id')
    def test_get_report_status(self, mock_find_by_id):
        """Test getting the status of a report."""
        # Configure mock
        mock_report = MagicMock(spec=Report)
        mock_report.id = 123
        mock_report.report_name = "Test Report"
        mock_report.report_type = "test"
        mock_report.status = "completed"
        mock_report.created_at = None
        mock_report.file_path = "/path/to/report.pdf"
        mock_find_by_id.return_value = mock_report
        
        with self.app.app_context():
            # Call the method
            status = self.report_service.get_report_status(123)
            
            # Assertions
            self.assertEqual(status['id'], 123)
            self.assertEqual(status['name'], "Test Report")
            self.assertEqual(status['type'], "test")
            self.assertEqual(status['status'], "completed")
            self.assertEqual(status['file_path'], "/path/to/report.pdf")
            mock_find_by_id.assert_called_once_with(123)
    
    @patch('app.models.report.Report.find_by_id')
    def test_get_report_status_not_found(self, mock_find_by_id):
        """Test getting the status of a non-existent report."""
        # Configure mock to return None
        mock_find_by_id.return_value = None
        
        with self.app.app_context():
            # Call the method
            status = self.report_service.get_report_status(999)
            
            # Assertions
            self.assertEqual(status['status'], "not_found")
            mock_find_by_id.assert_called_once_with(999)
    
    @patch('app.models.report_data.ReportData.find_by_report_id')
    def test_get_report_data(self, mock_find_by_report_id):
        """Test getting data for a report."""
        # Configure mock
        mock_data1 = MagicMock(spec=ReportData)
        mock_data1.to_dict.return_value = {"id": 1, "metric_name": "metric1", "metric_value": "100"}
        mock_data2 = MagicMock(spec=ReportData)
        mock_data2.to_dict.return_value = {"id": 2, "metric_name": "metric2", "metric_value": "200"}
        mock_find_by_report_id.return_value = [mock_data1, mock_data2]
        
        with self.app.app_context():
            # Call the method
            data = self.report_service.get_report_data(123)
            
            # Assertions
            self.assertEqual(len(data), 2)
            self.assertEqual(data[0]["id"], 1)
            self.assertEqual(data[1]["metric_name"], "metric2")
            mock_find_by_report_id.assert_called_once_with(123)
    
    @patch('app.models.report.Report.find_by_id')
    @patch('app.models.report_data.ReportData.delete_by_report_id')
    def test_delete_report(self, mock_delete_by_report_id, mock_find_by_id):
        """Test deleting a report."""
        # Configure mocks
        mock_report = MagicMock(spec=Report)
        mock_report.id = 123
        mock_report.file_path = os.path.join(self.temp_dir, "test_report.pdf")
        mock_find_by_id.return_value = mock_report
        mock_delete_by_report_id.return_value = 5  # 5 data records deleted
        
        # Create a dummy file to be deleted
        with open(mock_report.file_path, 'w') as f:
            f.write("test")
        
        with self.app.app_context():
            # Call the method
            result = self.report_service.delete_report(123)
            
            # Assertions
            self.assertTrue(result)
            mock_find_by_id.assert_called_once_with(123)
            mock_delete_by_report_id.assert_called_once_with(123)
            mock_report.delete.assert_called_once()
            self.assertFalse(os.path.exists(mock_report.file_path))
    
    @patch('app.models.report.Report.find_by_id')
    def test_delete_report_not_found(self, mock_find_by_id):
        """Test deleting a non-existent report."""
        # Configure mock to return None
        mock_find_by_id.return_value = None
        
        with self.app.app_context():
            # Call the method
            result = self.report_service.delete_report(999)
            
            # Assertions
            self.assertFalse(result)
            mock_find_by_id.assert_called_once_with(999)
    
    @patch('app.models.report.Report.find_all')
    def test_list_reports(self, mock_find_all):
        """Test listing all reports."""
        # Configure mock
        mock_report1 = MagicMock(spec=Report)
        mock_report1.to_dict.return_value = {"id": 1, "report_name": "Report 1"}
        mock_report2 = MagicMock(spec=Report)
        mock_report2.to_dict.return_value = {"id": 2, "report_name": "Report 2"}
        mock_find_all.return_value = [mock_report1, mock_report2]
        
        with self.app.app_context():
            # Call the method
            reports = self.report_service.list_reports()
            
            # Assertions
            self.assertEqual(len(reports), 2)
            self.assertEqual(reports[0]["id"], 1)
            self.assertEqual(reports[1]["report_name"], "Report 2")
            mock_find_all.assert_called_once_with(50, 0)
    
    @patch('app.models.report.Report.find_by_type')
    def test_list_reports_by_type(self, mock_find_by_type):
        """Test listing reports by type."""
        # Configure mock
        mock_report1 = MagicMock(spec=Report)
        mock_report1.to_dict.return_value = {"id": 1, "report_name": "Report 1", "report_type": "test"}
        mock_find_by_type.return_value = [mock_report1]
        
        with self.app.app_context():
            # Call the method
            reports = self.report_service.list_reports(report_type="test")
            
            # Assertions
            self.assertEqual(len(reports), 1)
            self.assertEqual(reports[0]["report_name"], "Report 1")
            mock_find_by_type.assert_called_once_with("test", 50, 0)


if __name__ == '__main__':
    unittest.main()