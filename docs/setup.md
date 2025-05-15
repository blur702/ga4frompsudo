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

## Running the Application

1. Start the development server:
   ```bash
   flask run
   # or
   python run.py
   ```

2. Access the application at `http://127.0.0.1:5000` (or the configured host/port)

3. Follow the on-screen instructions to authenticate with Google and start using the dashboard

## Running Tests

Execute the test suite using pytest:
```bash
pytest
```

Or run specific test files:
```bash
pytest tests/unit/models/test_database.py
```

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