"""
Models Initialization File.

This file makes the main model classes available directly under the
`app.models` package namespace, simplifying imports in other parts of
the application. It also defines the `__all__` special variable to
specify what symbols are exported when `from app.models import *` is used
(though explicit imports are generally preferred).
"""

# Import the primary Database utility class
from .database import Database

# Import the BaseModel class
from .base_model import BaseModel

# Import all specific model classes that inherit from BaseModel
from .property import Property
from .website import Website
from .report import Report
from .report_data import ReportData

# Define __all__ to specify the public interface of the models package.
# This list should include all classes and any other objects that are
# intended to be part of the public API of this package.
__all__ = [
    'Database',
    'BaseModel',
    'Property',
    'Website',
    'Report',
    'ReportData'
    # Add any other model classes here as they are created.
]

# Enable basic logging for model initialization
import logging
logger = logging.getLogger(__name__)
logger.debug("app.models package initialized and models imported.")