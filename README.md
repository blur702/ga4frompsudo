# GA4 Analytics Dashboard

A web application designed to fetch, process, and visualize Google Analytics 4 data for web properties. The application provides a plugin-based architecture for customizable analytics, dashboard visualizations, and report generation.

## Features

- Authentication with Google Analytics 4 API
- Secure service account authentication for GA4 integration
- Fetching and storing GA4 property data
- Modular plugin system for extensible analytics processing
- PDF and interactive report generation
- WCAG AA accessibility compliance
- Security features including encryption and token-based authentication

## Project Structure

The application follows the Model-View-Controller (MVC) architecture with a plugin system for extensible data processing:

```
app/
├── __init__.py         # Application factory
├── config.py           # Configuration settings
├── models/             # Database models
│   ├── base_model.py   # Abstract base model
│   ├── database.py     # Database connection manager
│   ├── property.py     # GA4 property model
│   ├── report.py       # Report model
│   ├── report_data.py  # Report data model
│   ├── user.py         # User model
│   └── website.py      # Website model
├── services/           # Business logic and API integration
│   ├── auth_service.py        # Authentication service
│   ├── ga4_service.py         # Google Analytics 4 service
│   ├── plugin_service.py      # Plugin management service
│   └── security_service.py    # Security and encryption service
├── plugins/            # Extensible analytics plugins
│   ├── base_plugin.py         # Base plugin class
│   └── engagement_metrics.py  # Sample engagement metrics plugin
├── controllers/        # Route controllers (to be implemented)
├── utils/              # Utility functions
│   ├── date_utils.py          # Date handling utilities
│   └── security_utils.py      # Security utilities
└── views/              # Templates and UI (to be implemented)
```

## Installation

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Configure environment variables in a `.env` file:
   ```
   FLASK_ENV=development
   FLASK_DEBUG=1
   SECRET_KEY=your-secret-key
   DATABASE_PATH=app.db
   GA4_CREDENTIALS_PATH=/path/to/ga4-credentials.json
   ENCRYPTION_KEY_PATH=/path/to/encryption.key
   ```

## Development

The project uses a test-driven development approach. Run tests with:

```
pytest
```

For coverage reporting:

```
coverage run -m pytest
coverage report
```

## Running the Application

### Before First Run

1. Generate an encryption key:

```bash
python generate_key.py
```

2. Create an admin user:

```bash
python create_admin_cli.py kevin.althaus@mail.house.gov password123 Kevin Althaus
```

3. Log in to the admin interface to configure GA4 credentials:
   - Navigate to http://127.0.0.1:5000/auth/login
   - Log in as kevin.althaus@mail.house.gov (passwordless login is enabled for admin users)
   - Go to Admin > GA4 Configuration
   - Paste your GA4 service account credentials JSON

4. To get GA4 service account credentials:
   - Create a service account in Google Cloud Console
   - Enable the Google Analytics Data API
   - Grant the service account appropriate access to your GA4 properties
   - Create and download a JSON key

5. Create a `.env` file based on `.env.example` with your configuration settings

### Starting the Development Server

Development mode:

```bash
python run.py
```

Or with Flask CLI:

```bash
flask run
```

### Access the Application

Open your browser and navigate to:
- http://127.0.0.1:5000/

### API Usage

The application provides a RESTful API for integration with other systems. All API endpoints require authentication using a bearer token:

```bash
curl -H "Authorization: Bearer YOUR_API_TOKEN" http://127.0.0.1:5000/api/properties
```

To generate an API token, use the admin interface or the API endpoint:

```bash
curl -X POST \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "scopes": ["read", "write"]}' \
  http://127.0.0.1:5000/api/tokens
```

## Implementation Status

### Completed
- ✅ Application factory pattern and configuration
- ✅ Database models and SQLite integration
- ✅ Threading-safe database connections
- ✅ User authentication system
- ✅ Security service with encryption/decryption
- ✅ GA4 service for Analytics API integration
- ✅ Plugin system architecture
- ✅ Sample engagement metrics plugin
- ✅ Date and security utilities
- ✅ Admin interface for application configuration
- ✅ Passwordless admin login for development
- ✅ UI for uploading GA4 credentials

### In Progress
- 🔄 Controllers and routing
- 🔄 Template and view structure
- 🔄 Report generation service
- 🔄 User management interface

### Planned
- 📅 API routes for plugin integration
- 📅 Advanced visualization support
- 📅 User management interface
- 📅 Additional analytics plugins
- 📅 Accessibility enhancements

## License

[License information to be added]