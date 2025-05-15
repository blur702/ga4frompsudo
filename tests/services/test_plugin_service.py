import unittest
from unittest.mock import patch, MagicMock

from flask import Flask

from app.services.plugin_service import PluginService
from app.plugins.base_plugin import BasePlugin


# Create a mock plugin for testing
class MockPlugin(BasePlugin):
    """Mock plugin for testing."""
    PLUGIN_ID = "mock_plugin"
    PLUGIN_NAME = "Mock Plugin"
    PLUGIN_DESCRIPTION = "A mock plugin for testing"
    
    def process_data(self, data):
        """Process data."""
        return {"processed": True, "data": data}
    
    def test_method(self, arg1, arg2=None):
        """Test method."""
        return {"arg1": arg1, "arg2": arg2}


class TestPluginService(unittest.TestCase):
    """Test suite for the PluginService class."""

    def setUp(self):
        """Set up the test environment before each test."""
        # Create a test Flask app
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.app.config['PLUGIN_PATHS'] = ['app.plugins', 'tests.services']
        
        # Create the plugin service
        with self.app.app_context():
            self.plugin_service = PluginService()
            
            # Add mock plugin to the plugins dictionary for testing
            self.plugin_service.plugins = {
                "mock_plugin": MockPlugin
            }

    @patch('importlib.import_module')
    def test_discover_plugins(self, mock_import_module):
        """Test discovering plugins from configured paths."""
        # Configure the mock
        mock_module = MagicMock()
        mock_module_attr = MagicMock()
        mock_module_attr.__name__ = "module_attr"
        
        # Set up the mock module with attributes
        mock_module.__name__ = "mock_module"
        mock_module.__dict__ = {"module_attr": mock_module_attr}
        mock_module.__all__ = ["module_attr"]
        
        # Set up dir() to return attributes
        def mock_dir(module):
            return ["module_attr", "_private_attr"]
            
        with patch('dir', mock_dir):
            mock_import_module.return_value = mock_module
            
            # Call the method
            with self.app.app_context():
                discovered = self.plugin_service.discover_plugins()
                
                # Assertions
                self.assertEqual(len(discovered), 2)  # Two configured paths
                mock_import_module.assert_any_call('app.plugins')
                mock_import_module.assert_any_call('tests.services')

    def test_get_plugin_class(self):
        """Test getting a plugin class by ID."""
        # Test with existing plugin
        plugin_class = self.plugin_service.get_plugin_class("mock_plugin")
        self.assertEqual(plugin_class, MockPlugin)
        
        # Test with non-existent plugin
        plugin_class = self.plugin_service.get_plugin_class("nonexistent_plugin")
        self.assertIsNone(plugin_class)

    def test_get_plugin_instance(self):
        """Test getting a plugin instance by ID."""
        # Test with existing plugin
        instance = self.plugin_service.get_plugin_instance("mock_plugin")
        self.assertIsInstance(instance, MockPlugin)
        self.assertEqual(instance.PLUGIN_ID, "mock_plugin")
        
        # Test with non-existent plugin
        instance = self.plugin_service.get_plugin_instance("nonexistent_plugin")
        self.assertIsNone(instance)
        
        # Test getting cached instance
        instance2 = self.plugin_service.get_plugin_instance("mock_plugin")
        self.assertIs(instance, instance2)  # Should be the same object

    def test_execute_plugin_method(self):
        """Test executing a method on a plugin instance."""
        # Test with existing method
        result = self.plugin_service.execute_plugin_method(
            "mock_plugin", "test_method", "value1", arg2="value2"
        )
        self.assertEqual(result["arg1"], "value1")
        self.assertEqual(result["arg2"], "value2")
        
        # Test with non-existent plugin
        result = self.plugin_service.execute_plugin_method(
            "nonexistent_plugin", "test_method", "value"
        )
        self.assertIsNone(result)
        
        # Test with non-existent method
        result = self.plugin_service.execute_plugin_method(
            "mock_plugin", "nonexistent_method", "value"
        )
        self.assertIsNone(result)
        
        # Test with method that raises an exception
        with patch.object(MockPlugin, 'test_method', side_effect=Exception("Test error")):
            result = self.plugin_service.execute_plugin_method(
                "mock_plugin", "test_method", "value"
            )
            self.assertIsNone(result)

    def test_process_data(self):
        """Test processing data with a plugin."""
        # Test with existing plugin
        result = self.plugin_service.execute_plugin_method(
            "mock_plugin", "process_data", {"test": "data"}
        )
        self.assertTrue(result["processed"])
        self.assertEqual(result["data"]["test"], "data")

    def test_get_available_plugins(self):
        """Test getting information about available plugins."""
        # Test with our mock plugin
        plugins_info = self.plugin_service.get_available_plugins()
        
        self.assertEqual(len(plugins_info), 1)
        self.assertIn("mock_plugin", plugins_info)
        
        mock_info = plugins_info["mock_plugin"]
        self.assertEqual(mock_info["id"], "mock_plugin")
        self.assertEqual(mock_info["name"], "Mock Plugin")
        self.assertEqual(mock_info["description"], "A mock plugin for testing")
        self.assertIn("version", mock_info)
        self.assertIn("author", mock_info)
        self.assertIn("category", mock_info)

    def test_reload_plugins(self):
        """Test reloading plugins."""
        # Add a plugin instance
        instance = self.plugin_service.get_plugin_instance("mock_plugin")
        self.assertIsInstance(instance, MockPlugin)
        
        # Reload plugins
        with patch.object(self.plugin_service, 'register_plugins') as mock_register:
            self.plugin_service.reload_plugins()
            
            # Assertions
            self.assertEqual(len(self.plugin_service.plugins), 0)
            self.assertEqual(len(self.plugin_service.plugin_instances), 0)
            mock_register.assert_called_once()


if __name__ == '__main__':
    unittest.main()