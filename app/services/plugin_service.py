import logging
import importlib
import inspect
from typing import Dict, List, Type, Any, Optional

from flask import current_app

logger = logging.getLogger(__name__)

class PluginService:
    """
    Service for managing and executing plugins in the application.
    
    This service provides methods to:
    - Discover and register plugins
    - Execute plugin methods
    - Manage plugin configurations
    - Handle plugin dependencies
    """
    
    def __init__(self):
        """Initialize the Plugin Service."""
        self.plugins = {}
        self.plugin_instances = {}
        self.plugin_paths = current_app.config.get('PLUGIN_PATHS', ['app.plugins'])
        
        logger.info("Plugin Service initialized")
    
    def discover_plugins(self) -> List[str]:
        """
        Discover available plugins from the configured plugin paths.
        
        Returns:
            List of plugin module names
        """
        discovered_plugins = []
        
        for path in self.plugin_paths:
            try:
                module = importlib.import_module(path)
                
                # Get all attributes in the module
                for attr_name in dir(module):
                    # Skip private attributes
                    if attr_name.startswith('_'):
                        continue
                    
                    attr = getattr(module, attr_name)
                    
                    # Check if it's a module
                    if inspect.ismodule(attr):
                        discovered_plugins.append(f"{path}.{attr_name}")
            except ImportError as e:
                logger.warning(f"Could not import plugin path {path}: {e}")
        
        logger.info(f"Discovered {len(discovered_plugins)} plugin modules: {discovered_plugins}")
        return discovered_plugins
    
    def register_plugins(self) -> None:
        """
        Register all discovered plugins.
        """
        plugin_modules = self.discover_plugins()
        
        for module_name in plugin_modules:
            try:
                module = importlib.import_module(module_name)
                
                # Look for plugin classes (anything with a PLUGIN_ID attribute)
                for attr_name in dir(module):
                    if attr_name.startswith('_'):
                        continue
                    
                    attr = getattr(module, attr_name)
                    
                    # Check if it's a class that has a PLUGIN_ID
                    if inspect.isclass(attr) and hasattr(attr, 'PLUGIN_ID'):
                        plugin_id = getattr(attr, 'PLUGIN_ID')
                        self.plugins[plugin_id] = attr
                        logger.debug(f"Registered plugin: {plugin_id} ({attr.__name__})")
            except ImportError as e:
                logger.warning(f"Could not import plugin module {module_name}: {e}")
        
        logger.info(f"Registered {len(self.plugins)} plugins: {list(self.plugins.keys())}")
    
    def get_plugin_class(self, plugin_id: str) -> Optional[Type]:
        """
        Get the plugin class by its ID.
        
        Args:
            plugin_id: The plugin ID
            
        Returns:
            Plugin class if found, None otherwise
        """
        return self.plugins.get(plugin_id)
    
    def get_plugin_instance(self, plugin_id: str) -> Any:
        """
        Get or create a plugin instance by its ID.
        
        Args:
            plugin_id: The plugin ID
            
        Returns:
            Plugin instance if found, None otherwise
        """
        # Return existing instance if already created
        if plugin_id in self.plugin_instances:
            return self.plugin_instances[plugin_id]
        
        # Get the plugin class
        plugin_class = self.get_plugin_class(plugin_id)
        if not plugin_class:
            logger.warning(f"Plugin {plugin_id} not found")
            return None
        
        # Create the plugin instance
        try:
            plugin_instance = plugin_class()
            self.plugin_instances[plugin_id] = plugin_instance
            logger.debug(f"Created instance of plugin {plugin_id}")
            return plugin_instance
        except Exception as e:
            logger.error(f"Failed to create instance of plugin {plugin_id}: {e}", exc_info=True)
            return None
    
    def execute_plugin_method(self, plugin_id: str, method_name: str, *args, **kwargs) -> Any:
        """
        Execute a method on a plugin instance.
        
        Args:
            plugin_id: The plugin ID
            method_name: The method name to execute
            *args: Positional arguments to pass to the method
            **kwargs: Keyword arguments to pass to the method
            
        Returns:
            The result of the method execution
        """
        plugin_instance = self.get_plugin_instance(plugin_id)
        if not plugin_instance:
            logger.warning(f"Cannot execute method {method_name} on plugin {plugin_id}: plugin not found")
            return None
        
        if not hasattr(plugin_instance, method_name):
            logger.warning(f"Plugin {plugin_id} does not have method {method_name}")
            return None
        
        try:
            method = getattr(plugin_instance, method_name)
            return method(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error executing {method_name} on plugin {plugin_id}: {e}", exc_info=True)
            return None
    
    def get_available_plugins(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all available plugins.
        
        Returns:
            Dictionary of plugin information, keyed by plugin ID
        """
        plugins_info = {}
        
        for plugin_id, plugin_class in self.plugins.items():
            plugins_info[plugin_id] = {
                'id': plugin_id,
                'name': getattr(plugin_class, 'PLUGIN_NAME', plugin_id),
                'description': getattr(plugin_class, 'PLUGIN_DESCRIPTION', ''),
                'version': getattr(plugin_class, 'PLUGIN_VERSION', '1.0.0'),
                'author': getattr(plugin_class, 'PLUGIN_AUTHOR', ''),
                'category': getattr(plugin_class, 'PLUGIN_CATEGORY', 'Unknown')
            }
        
        return plugins_info
    
    def reload_plugins(self) -> None:
        """
        Reload all plugins by clearing the registry and rediscovering plugins.
        """
        logger.info("Reloading plugins...")
        self.plugins = {}
        self.plugin_instances = {}
        self.register_plugins()