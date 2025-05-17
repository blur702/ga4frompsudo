# Setup Instructions

This document provides detailed instructions for setting up and running the GA4 Analytics Dashboard application.

## Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- A Google Account with access to Google Analytics 4 properties
- Google API credentials for accessing GA4 API

## Installation

1. Clone the repository:
   ```bash
   git clone [repository-url]
   cd ga4-analytics-dashboard
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file by copying the example file:
   ```bash
   cp .env.example .env
   ```

5. Update the `.env` file with your specific configuration:
   - Set a secure `SECRET_KEY`
   - Configure Google API credentials (`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, etc.)
   - Set database path if different from default
   - Configure other environment-specific settings

## Google API Setup

1. Go to the [Google API Console](https://console.developers.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Analytics Admin API and Google Analytics Data API
4. Create OAuth 2.0 credentials (web application type)
5. Set the authorized redirect URI to match your `GOOGLE_REDIRECT_URI` configuration
6. Add the client ID and client secret to your `.env` file

## Database Initialization

The database is automatically initialized when the application starts for the first time. It will create the necessary tables in the SQLite database specified in the configuration.

## Creating Admin User

Before accessing the application, you need to create an admin user:

1. Use the provided command-line utility:
   ```bash
   python create_admin_cli.py <email> <password> [first_name] [last_name]
   ```

2. Example:
   ```bash
   python create_admin_cli.py admin@example.com SecureP@ss123 Admin User
   ```

3. Password requirements:
   - Minimum 8 characters
   - Must include uppercase letters
   - Must include lowercase letters
   - Must include numbers
   - Must include special characters

This admin user will have full access to the application and can create additional users as needed.

## Running the Application

1. Start the development server:
   ```bash
   flask run
   # or
   python run.py
   ```

2. Access the application at `http://127.0.0.1:5000` (or the configured host/port)

3. Log in with the admin user credentials you created in the previous step

4. Follow the on-screen instructions to authenticate with Google and start using the dashboard

## Running Tests

Execute the test suite using pytest:
```bash
pytest
```

Or run specific test files:
```bash
pytest tests/unit/models/test_database.py
```

## Troubleshooting

### Login Issues
- If you cannot log in, verify the user was created successfully
- Check application logs for any authentication errors
- Try recreating the admin user with a new password

### Database Issues
- If database tables aren't created automatically, check the application logs
- Ensure the database path is writable by the application user

### GA4 API Access
- Verify your GA4 credentials path is correctly set in config
- Ensure the service account has proper permissions in Google Analytics

## Deployment Considerations

For production deployment:

1. Update the `.env` configuration with:
   - Set `FLASK_ENV=production`
   - Use a proper production-ready database
   - Configure appropriate logging
   - Generate a strong, unique SECRET_KEY

2. Use a WSGI server like Gunicorn:
   ```bash
   gunicorn --bind 0.0.0.0:5000 "run:app"
   ```

3. Consider using a reverse proxy like Nginx for enhanced security and performance

4. Implement proper security measures for handling credentials and tokens in production