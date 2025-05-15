"""
GA4 Analytics Dashboard entry point.
This is a simple wrapper around run.py to maintain compatibility.
"""

from run import app

# Import models, services, and plugins for shell context and convenience
from app.models.database import Database
from app.models.user import User
from app.models.property import Property
from app.models.website import Website
from app.models.report import Report
from app.models.report_data import ReportData

from app.services.security_service import SecurityService
from app.services.auth_service import AuthService
from app.services.ga4_service import GA4Service
from app.services.plugin_service import PluginService

from app.plugins.base_plugin import BasePlugin
from app.plugins.engagement_metrics import EngagementMetricsPlugin

# This ensures that app.py is equivalent to run.py for backward compatibility
@app.route('/')
def hello_world():
    return 'Hello from GA4 Analytics Dashboard!'

if __name__ == '__main__':
    app.run()
