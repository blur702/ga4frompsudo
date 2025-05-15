"""
Utilities Initialization File (app/utils/__init__.py).

This file makes key utility functions and classes from the various utility
modules (date_utils, security_utils, accessibility_utils, formatters)
directly accessible under the `app.utils` package namespace.
This simplifies import statements in other parts of the application.
For example, instead of `from app.utils.date_utils import parse_date_range`,
one can use `from app.utils import parse_date_range`.

It also defines the `__all__` special variable, which specifies the public symbols
that are exported when a wildcard import (`from app.utils import *`) is used.
While explicit imports are generally preferred, `__all__` is good practice for
defining a clear public API for the package.
"""

import logging
from flask import Flask

# Import functions and classes from date_utils.py
from .date_utils import (
    parse_date_range,
    format_date_for_ga4,
    get_date_periods,
    format_date_for_display
)

# Import functions from security_utils.py
from .security_utils import (
    generate_secure_token,
    generate_fernet_encryption_key,
    hash_password,
    verify_password,
    encrypt_data,
    decrypt_data,
    sanitize_input,
    is_valid_email,
    is_valid_password
)

# Import functions from accessibility_utils.py
from .accessibility_utils import (
    check_contrast_compliance,
    generate_alt_text,
    create_aria_attributes,
    accessibility_audit,
    generate_skip_link,
    set_lang_attribute
)

# Import functions from formatters.py
from .formatters import (
    format_number,
    format_percentage,
    format_date,
    format_duration,
    format_file_size,
    format_metric_name,
    data_to_csv,
    data_to_json,
    format_ga4_report_data
)

# Define __all__ to specify the public interface of the utils package.
__all__ = [
    # From date_utils
    'parse_date_range',
    'format_date_for_ga4',
    'get_date_periods',
    'format_date_for_display',
    
    # From security_utils
    'generate_secure_token',
    'generate_fernet_encryption_key',
    'hash_password',
    'verify_password',
    'encrypt_data',
    'decrypt_data',
    'sanitize_input',
    'is_valid_email',
    'is_valid_password',
    
    # From accessibility_utils
    'check_contrast_compliance',
    'generate_alt_text',
    'create_aria_attributes',
    'accessibility_audit',
    'generate_skip_link',
    'set_lang_attribute',
    
    # From formatters
    'format_number',
    'format_percentage',
    'format_date',
    'format_duration',
    'format_file_size',
    'format_metric_name',
    'data_to_csv',
    'data_to_json',
    'format_ga4_report_data',
    
    # Initialization
    'init_utils'
]

# Log that the utils package has been initialized.
logger = logging.getLogger(__name__)
logger.debug("app.utils package initialized. Exporting: %s", ", ".join(__all__))

def init_utils(app: Flask) -> None:
    """
    Initialize any utility modules that require setup.
    
    Args:
        app: The Flask application instance
    """
    logger.info("Initializing utility modules...")
    
    # Currently, our utility modules don't need initialization,
    # but this function provides a hook for future expansion
    
    # Register template filters for formatters
    register_template_filters(app)
    
    logger.info("Utility modules initialized successfully")

def register_template_filters(app: Flask) -> None:
    """
    Register template filters from the formatter module.
    
    Args:
        app: The Flask application instance
    """
    # Register basic formatters
    app.template_filter('format_number')(format_number)
    app.template_filter('format_percentage')(format_percentage)
    app.template_filter('format_date')(format_date)
    app.template_filter('format_duration')(format_duration)
    app.template_filter('format_file_size')(format_file_size)
    app.template_filter('format_metric_name')(format_metric_name)
    
    logger.debug("Registered formatter template filters")
    
    # Register HTML/accessibility helpers
    app.template_filter('check_contrast')(check_contrast_compliance)
    app.template_filter('alt_text')(generate_alt_text)
    app.template_filter('aria_attrs')(create_aria_attributes)
    
    logger.debug("Registered accessibility template filters")