"""
Services package for the GA4 Analytics Dashboard.

This package contains service classes that provide business logic and integration
with external APIs and systems.
"""

import logging
import os
from typing import Dict, Any, Optional

from flask import Flask, current_app

from app.services.security_service import SecurityService
from app.services.auth_service import AuthService
from app.services.ga4_service import GA4Service
from app.services.plugin_service import PluginService
from app.services.report_service import ReportService

logger = logging.getLogger(__name__)

# Global service registry
_services = {}

def init_services(app: Flask) -> None:
    """
    Initialize all application services and store them in the services registry.
    
    Args:
        app: The Flask application instance
    """
    logger.info("Initializing application services...")
    
    # Initialize the security service first as other services depend on it
    security_service = SecurityService(
        key_file_path=app.config.get('ENCRYPTION_KEY_PATH'),
        salt=app.config.get('PASSWORD_SALT', 'default_salt_change_me')
    )
    _services['security'] = security_service
    logger.info("Security service initialized")
    
    # Initialize authentication service
    auth_service = AuthService(security_service)
    _services['auth'] = auth_service
    logger.info("Authentication service initialized")
    
    # Initialize GA4 service if credentials are available
    ga4_credentials_path = app.config.get('GA4_CREDENTIALS_PATH')
    if ga4_credentials_path and os.path.exists(ga4_credentials_path):
        ga4_service = GA4Service(credentials_path=ga4_credentials_path)
        _services['ga4'] = ga4_service
        logger.info("GA4 service initialized")
    else:
        logger.warning(f"GA4 service not initialized: credentials not found at {ga4_credentials_path}")
    
    # Initialize plugin service
    plugin_service = PluginService()
    _services['plugin'] = plugin_service
    logger.info("Plugin service initialized")
    
    # Initialize report service
    report_service = ReportService()
    _services['report'] = report_service
    logger.info("Report service initialized")
    
    logger.info("All services initialized successfully")

def get_service(service_name: str) -> Optional[Any]:
    """
    Get a service instance by name from the service registry.
    
    Args:
        service_name: Name of the service to retrieve
        
    Returns:
        Service instance if found, None otherwise
    """
    return _services.get(service_name)

def get_services() -> Dict[str, Any]:
    """
    Get all services in the registry.
    
    Returns:
        Dictionary of all registered services
    """
    return _services.copy()  # Return a copy to prevent modification