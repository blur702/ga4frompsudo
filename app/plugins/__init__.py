"""
Plugins package for the GA4 Analytics Dashboard.

This package contains plugin classes that add functionality to the application.
Plugins can register for specific hooks and extend the dashboard with custom
features, reports, and integrations.
"""

# Import all plugin modules for automatic discovery
from app.plugins.base_plugin import BasePlugin
from app.plugins.engagement_metrics import EngagementMetricsPlugin

# List of plugin classes available in this package
__all__ = [
    'BasePlugin',
    'EngagementMetricsPlugin',
]