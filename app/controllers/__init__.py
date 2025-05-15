"""
Controllers package for the GA4 Analytics Dashboard.

This package contains the route controllers that define the application's
URL endpoints and handle incoming HTTP requests.
"""

import logging
from typing import Dict, List

from flask import Flask, Blueprint

logger = logging.getLogger(__name__)

# Store all registered blueprints
_blueprints: Dict[str, Blueprint] = {}

def init_controllers(app: Flask) -> None:
    """
    Initialize and register all controllers/blueprints with the Flask app.
    
    Args:
        app: The Flask application instance
    """
    logger.info("Initializing controllers...")
    
    # Import the controllers here to avoid circular imports
    from app.controllers.auth_controller import auth_bp
    from app.controllers.dashboard_controller import dashboard_bp
    from app.controllers.reports_controller import reports_bp
    from app.controllers.api_controller import api_bp
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    _blueprints['auth'] = auth_bp
    logger.info("Registered auth blueprint")
    
    app.register_blueprint(dashboard_bp)
    _blueprints['dashboard'] = dashboard_bp
    logger.info("Registered dashboard blueprint")
    
    app.register_blueprint(reports_bp)
    _blueprints['reports'] = reports_bp
    logger.info("Registered reports blueprint")
    
    app.register_blueprint(api_bp, url_prefix='/api')
    _blueprints['api'] = api_bp
    logger.info("Registered API blueprint")
    
    logger.info("All controllers initialized successfully")

def get_blueprints() -> Dict[str, Blueprint]:
    """
    Get all registered blueprints.
    
    Returns:
        Dictionary of blueprint name to Blueprint instance
    """
    return _blueprints.copy()

def get_blueprint(name: str) -> Blueprint:
    """
    Get a specific blueprint by name.
    
    Args:
        name: Name of the blueprint
        
    Returns:
        Blueprint instance if found, None otherwise
    """
    return _blueprints.get(name)