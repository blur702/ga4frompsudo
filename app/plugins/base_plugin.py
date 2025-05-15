import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class BasePlugin(ABC):
    """
    Base class for all GA4 Analytics Dashboard plugins.
    
    Plugins extend the functionality of the dashboard by implementing specific
    data processing, visualization, or integration features.
    
    Attributes:
        PLUGIN_ID: Unique identifier for the plugin (must be overridden)
        PLUGIN_NAME: Human-readable name (defaults to class name)
        PLUGIN_VERSION: Version string (defaults to 1.0.0)
        PLUGIN_DESCRIPTION: Human-readable description
        PLUGIN_AUTHOR: Author or organization name
        PLUGIN_CATEGORY: Category for grouping plugins
    """
    
    # Plugin metadata that should be overridden by subclasses
    PLUGIN_ID = None  # Required
    PLUGIN_NAME = None  # Optional, will default to class name
    PLUGIN_VERSION = "1.0.0"  # Optional
    PLUGIN_DESCRIPTION = ""  # Optional
    PLUGIN_AUTHOR = ""  # Optional
    PLUGIN_CATEGORY = "General"  # Optional
    
    def __init__(self):
        """Initialize the plugin."""
        if self.PLUGIN_ID is None:
            raise ValueError(f"Plugin {self.__class__.__name__} must define PLUGIN_ID")
        
        # Set default name if not provided
        if self.PLUGIN_NAME is None:
            self.PLUGIN_NAME = self.__class__.__name__
            
        self.config = {}
        logger.debug(f"Initialized plugin: {self.PLUGIN_ID} ({self.PLUGIN_NAME})")
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get plugin metadata.
        
        Returns:
            Dictionary containing plugin metadata
        """
        return {
            "id": self.PLUGIN_ID,
            "name": self.PLUGIN_NAME,
            "version": self.PLUGIN_VERSION,
            "description": self.PLUGIN_DESCRIPTION,
            "author": self.PLUGIN_AUTHOR,
            "category": self.PLUGIN_CATEGORY
        }
    
    def configure(self, config: Dict[str, Any]) -> None:
        """
        Configure the plugin with the provided settings.
        
        Args:
            config: Dictionary of configuration parameters
        """
        self.config.update(config)
        logger.debug(f"Configured plugin {self.PLUGIN_ID} with {len(config)} parameters")
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get the current plugin configuration.
        
        Returns:
            Dictionary of configuration parameters
        """
        return self.config.copy()
    
    def get_default_config(self) -> Dict[str, Any]:
        """
        Get the default configuration for this plugin.
        
        Returns:
            Dictionary of default configuration parameters
        """
        return {}
    
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """
        Validate the provided configuration.
        
        Args:
            config: Dictionary of configuration parameters to validate
            
        Returns:
            List of error messages (empty if configuration is valid)
        """
        return []  # Default implementation assumes all configurations are valid
    
    @abstractmethod
    def process_data(self, data: Any) -> Any:
        """
        Process the input data and return the result.
        
        This is the main entry point for plugin functionality and must be
        implemented by all plugin subclasses.
        
        Args:
            data: Input data to process
            
        Returns:
            Processed data
        """
        pass  # Must be implemented by subclasses
    
    def get_required_permissions(self) -> List[str]:
        """
        Get the list of permissions required by this plugin.
        
        Returns:
            List of permission strings
        """
        return []  # Default implementation requires no permissions
    
    def get_templates(self) -> Dict[str, str]:
        """
        Get templates provided by this plugin.
        
        Returns:
            Dictionary mapping template names to template paths
        """
        return {}  # Default implementation provides no templates
    
    def get_scripts(self) -> List[str]:
        """
        Get JavaScript files provided by this plugin.
        
        Returns:
            List of JavaScript file paths
        """
        return []  # Default implementation provides no scripts
    
    def get_styles(self) -> List[str]:
        """
        Get CSS files provided by this plugin.
        
        Returns:
            List of CSS file paths
        """
        return []  # Default implementation provides no styles
    
    def get_api_routes(self) -> List[Dict[str, Any]]:
        """
        Get API routes provided by this plugin.
        
        Returns:
            List of route dictionaries, each containing:
            - path: Route path
            - method: HTTP method
            - handler: Function to handle the route
            - auth_required: Whether authentication is required
        """
        return []  # Default implementation provides no API routes
    
    def on_activation(self) -> bool:
        """
        Called when the plugin is activated.
        
        Returns:
            True if activation was successful, False otherwise
        """
        logger.info(f"Plugin {self.PLUGIN_ID} activated")
        return True
    
    def on_deactivation(self) -> bool:
        """
        Called when the plugin is deactivated.
        
        Returns:
            True if deactivation was successful, False otherwise
        """
        logger.info(f"Plugin {self.PLUGIN_ID} deactivated")
        return True