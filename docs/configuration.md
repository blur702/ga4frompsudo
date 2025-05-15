# Configuration

This document outlines the configuration options available for the GA4 Analytics Dashboard application.

## Configuration Classes

The application uses configuration classes to handle different environments:

- `Config`: Base configuration class with common settings
- `DevelopmentConfig`: Configuration for development environment
- `TestingConfig`: Configuration for testing environment
- `ProductionConfig`: Configuration for production environment

## Environment Variables

The application is configured using environment variables. These can be set in a `.env` file, in the system environment, or passed to the application at runtime.

### Core Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | The environment to run the application in (`development`, `testing`, `production`) | `development` |
| `FLASK_APP` | The Flask application entry point | `run.py` |
| `SECRET_KEY` | Secret key for session signing and security | Random generated key |
| `APP_NAME` | The name of the application | `GA4 Analytics Dashboard` |
| `DATABASE_PATH` | Path to the SQLite database file | `ga4_dashboard.db` |
| `LOG_LEVEL` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`) | `INFO` |

### Google OAuth Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_CLIENT_ID` | Client ID from Google API Console | None |
| `GOOGLE_CLIENT_SECRET` | Client secret from Google API Console | None |
| `GOOGLE_REDIRECT_URI` | Redirect URI for OAuth callback | None |

### Security Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `ENCRYPTION_KEY_PATH` | Path to the encryption key file | `../security/encryption_app.key` |
| `PASSWORD_SALT_STATIC` | Static salt for non-user-specific cryptographic operations | Random generated salt |
| `TOKEN_LIFETIME_HOURS` | Lifetime of user session tokens in hours | `12` |

### Development and Testing

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_DEBUG` | Whether to enable Flask debug mode | `0` (disabled) |
| `FLASK_RUN_HOST` | Host to run the development server on | `127.0.0.1` |
| `FLASK_RUN_PORT` | Port to run the development server on | `5000` |

## Configuration Details

### DevelopmentConfig

Settings optimized for development:
- Debug mode enabled
- Templates auto-reload enabled
- Verbose logging (DEBUG level)

### TestingConfig

Settings optimized for testing:
- In-memory SQLite database
- CSRF protection disabled
- Testing server name set to `localhost.test`
- Mock OAuth credentials

### ProductionConfig

Settings optimized for production:
- Debug and testing mode disabled
- HTTPS enforced
- Less verbose logging (WARNING level)
- Option for more robust session management (commented out by default)

## Sample Configuration File (.env)

```
# Flask Configuration
FLASK_ENV=development
FLASK_APP=run.py
FLASK_DEBUG=1
FLASK_RUN_HOST=127.0.0.1
FLASK_RUN_PORT=5000

# Application Security
SECRET_KEY=your-secret-key-here
PASSWORD_SALT_STATIC=your-static-salt-here
TOKEN_LIFETIME_HOURS=12

# Database Configuration
DATABASE_PATH=ga4_dashboard.db

# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://127.0.0.1:5000/auth/callback

# Logging
LOG_LEVEL=DEBUG
```

## Loading Configuration

The application loads configuration in the following order:

1. Default values defined in the configuration classes
2. Environment variables
3. Configuration method overrides (when applicable)

## Accessing Configuration

Configuration values can be accessed in the application code via the Flask app's config dictionary:

```python
# Example
app.config['SECRET_KEY']  # Access the secret key
app.config.get('LOG_LEVEL', 'INFO')  # Access with default fallback
```