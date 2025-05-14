# 02 - Application Configuration

This file details the pseudocode for the application configuration module.
Target file: `app/config.py`

## Pseudocode (from `app-initialization-pseudocode.md`, refined in previous turns)

```python
"""
Application configuration.
Contains different configuration environments for the Flask app.
"""

import os
import secrets
import tempfile # Added for TestingConfig
from datetime import timedelta

class Config:
    """Base configuration class. Other configurations inherit from this."""

    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    APP_NAME = os.environ.get('APP_NAME', 'GA4 Analytics Dashboard')

    # Default database path, can be overridden by specific configs or environment variables
    DATABASE_PATH = os.environ.get('DATABASE_PATH') or os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'ga4_dashboard.db')


    # Google OAuth Configuration
    AUTH = {
        'client_id': os.environ.get('GOOGLE_CLIENT_ID'),
        'client_secret': os.environ.get('GOOGLE_CLIENT_SECRET'),
        'redirect_uri': os.environ.get('GOOGLE_REDIRECT_URI'), # e.g., 'http://localhost:5000/auth/callback'
        'token_uri': '[https://oauth2.googleapis.com/token](https://oauth2.googleapis.com/token)',
        'auth_uri': '[https://accounts.google.com/o/oauth2/auth](https://accounts.google.com/o/oauth2/auth)',
        'scope': [
            '[https://www.googleapis.com/auth/analytics.readonly](https://www.googleapis.com/auth/analytics.readonly)',
            '[https://www.googleapis.com/auth/analytics](https://www.googleapis.com/auth/analytics)' # For potential future admin operations if needed
        ]
    }

    # Security-related configurations
    SECURITY = {
        'key_path': os.environ.get('ENCRYPTION_KEY_PATH') or os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'security', 'encryption_app.key'),
        # Static salt for specific non-user cases if any.
        # For user passwords, salts should be generated per user and stored with the hash.
        'password_salt_static': os.environ.get('PASSWORD_SALT_STATIC') or secrets.token_hex(16),
        'token_lifetime': timedelta(hours=int(os.environ.get('TOKEN_LIFETIME_HOURS', '12'))) # For user session tokens
    }

    # Logging Configuration (basic, can be expanded)
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()


    @staticmethod
    def init_app(app):
        """
        Initialize application with this configuration.
        Can be used for any setup that needs the app instance.

        Args:
            app (Flask): Flask application instance.
        """
        # Example: Create directory for encryption key if it doesn't exist
        security_config = app.config.get('SECURITY', {})
        key_path = security_config.get('key_path')
        if key_path:
            key_dir = os.path.dirname(key_path)
            if not os.path.exists(key_dir):
                try:
                    os.makedirs(key_dir, exist_ok=True)
                    app.logger.info(f"Created directory for encryption key: {key_dir}")
                except OSError as e:
                    app.logger.error(f"Could not create directory {key_dir} for encryption key: {e}")
        pass

class DevelopmentConfig(Config):
    """Development configuration settings."""

    DEBUG = True
    TEMPLATES_AUTO_RELOAD = True # Reload templates automatically during development
    LOG_LEVEL = 'DEBUG' # More verbose logging for development

    @staticmethod
    def init_app(app):
        """Initialize development-specific app settings."""
        Config.init_app(app)
        app.logger.info("DevelopmentConfig initialized and applied.")
        # Example: app.logger.setLevel(logging.DEBUG) if not handled by basicConfig


class TestingConfig(Config):
    """Testing configuration settings."""

    TESTING = True
    DEBUG = True # Often useful for debugging tests, though can be False
    DATABASE_PATH = ':memory:' # Use an in-memory SQLite database for tests
    WTF_CSRF_ENABLED = False # Disable CSRF protection in forms for simpler testing
    SERVER_NAME = 'localhost.test' # Helps url_for generate URLs correctly in tests
    TEMPLATES_AUTO_RELOAD = True
    LOG_LEVEL = 'DEBUG' # Or 'ERROR' if too much test noise

    # Override OAuth credentials for testing (can be dummy values if OAuth flow is mocked)
    AUTH = { # type: ignore
        'client_id': 'test_google_client_id',
        'client_secret': 'test_google_client_secret',
        'redirect_uri': '[http://localhost.test/auth/callback](http://localhost.test/auth/callback)',
        'token_uri': '[https://example.com/oauth/token](https://example.com/oauth/token)', # Mocked endpoint
        'auth_uri': '[https://example.com/oauth/auth](https://example.com/oauth/auth)',   # Mocked endpoint
        'scope': Config.AUTH['scope'] # Keep scopes if they affect logic
    }

    # Use a temporary file for the encryption key during testing
    # This ensures tests don't rely on or create persistent files in the project structure.
    _temp_key_file = tempfile.NamedTemporaryFile(delete=False, suffix='.key')
    SECURITY = { # type: ignore
        **Config.SECURITY,
        'key_path': _temp_key_file.name,
    }
    _temp_key_file.close() # Close the file handle, but the file remains


    @staticmethod
    def init_app(app):
        """Initialize testing-specific app settings."""
        Config.init_app(app)
        app.logger.info("TestingConfig initialized and applied.")
        # Any additional app setup specific to testing can go here.

class ProductionConfig(Config):
    """Production configuration settings."""

    DEBUG = False
    TESTING = False
    PREFERRED_URL_SCHEME = 'https' # Ensure generated URLs use HTTPS in production
    LOG_LEVEL = 'WARNING' # Less verbose logging for production

    # Consider more robust session management, e.g., server-side sessions
    # SESSION_TYPE = 'filesystem'
    # SESSION_FILE_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'flask_session')


    @staticmethod
    def init_app(app):
        """Initialize production-specific app settings."""
        Config.init_app(app)
        # Example: Setup production logging (e.g., to a file or external service)
        # if not os.path.exists(app.config.get('SESSION_FILE_DIR', 'flask_session')):
        #     os.makedirs(app.config.get('SESSION_FILE_DIR', 'flask_session'), exist_ok=True)
        app.logger.info("ProductionConfig initialized and applied.")


# Dictionary mapping configuration names to their respective classes
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig # Default configuration if none is specified
}
```
