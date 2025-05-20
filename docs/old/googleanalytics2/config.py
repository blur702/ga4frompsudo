import os
from datetime import timedelta

class Config:
    """Base configuration class."""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 't')
    
    # Security settings
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = os.environ.get('WTF_CSRF_SECRET_KEY', SECRET_KEY)
    
    # Session security
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() in ('true', '1', 't')
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    
    # Database settings
    DATABASE_URI = os.environ.get('DATABASE_URI', 'sqlite:///ga4_dashboard.db')
    
    # Google OAuth settings
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
    
    # If OAuth credentials are not available, the application will fall back to using the API key
    # This allows for authentication even when OAuth is not configured
    OAUTH_FALLBACK_ENABLED = True
    
    # API Key security settings
    API_KEY_MIN_LENGTH = 20
    API_KEY_MAX_ATTEMPTS = 5  # Maximum number of failed API key attempts before temporary lockout
    API_KEY_LOCKOUT_TIME = 300  # Lockout time in seconds (5 minutes)
    
    # Session settings
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    
    # PDF generation settings
    WKHTMLTOPDF_PATH = os.environ.get('WKHTMLTOPDF_PATH', '/usr/local/bin/wkhtmltopdf')
    
    # File paths
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    REPORTS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reports')
    LOGS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    
    # Ensure directories exist
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(REPORTS_FOLDER, exist_ok=True)
    os.makedirs(LOGS_FOLDER, exist_ok=True)
    
    # API settings
    API_REQUEST_TIMEOUT = 60  # seconds
    MAX_CONCURRENT_REQUESTS = 5

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    
    # In production, ensure SECRET_KEY is set in environment
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # Use a more robust database in production
    DATABASE_URI = os.environ.get('DATABASE_URI', 'postgresql://user:password@localhost/ga4_dashboard')
    
    # Set secure cookie
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True
    
    # Content Security Policy
    CONTENT_SECURITY_POLICY = {
        'default-src': "'self'",
        'script-src': ["'self'", "'unsafe-inline'", "cdn.jsdelivr.net", "cdn.tailwindcss.com"],
        'style-src': ["'self'", "'unsafe-inline'", "cdn.tailwindcss.com"],
        'img-src': ["'self'", "data:"],
        'font-src': ["'self'"]
    }

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True
    
    # Use in-memory SQLite for testing
    DATABASE_URI = 'sqlite:///:memory:'

# Default to development config
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

# Set active configuration based on environment
active_config = config.get(os.environ.get('FLASK_ENV', 'default'))