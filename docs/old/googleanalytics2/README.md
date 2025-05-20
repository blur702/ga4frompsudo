# Google Analytics 4 Dashboard

A Flask-based web application for enhanced analytics reporting and visualization of Google Analytics 4 data.

## Overview

The Google Analytics 4 Dashboard provides enhanced analytics reporting and visualization capabilities beyond what is available in the standard Google Analytics 4 interface. It offers a more flexible and customizable way to analyze GA4 data, with features specifically designed for organizations managing multiple properties.

## Features

- **Authentication with Google OAuth 2.0**: Secure access to your Google Analytics data
- **Multiple GA4 Properties Management**: View and manage all your GA4 properties in one place
- **Comprehensive Reporting**: Generate various types of reports with customizable metrics and dimensions
  - URL Analytics Reports
  - Property Aggregation Reports
  - Device Reports
  - Geolocation Reports
  - And more
- **PDF Generation**: Export reports as PDF with executive summaries and screenshots
- **Data Visualization**: Interactive charts and graphs for better insights
- **Property Selection Sets**: Group properties for easier reporting
- **Caching**: Reduce API calls and improve performance

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Google Cloud Platform account with Google Analytics API enabled
- OAuth 2.0 credentials for Google API

### Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/ga4-dashboard.git
   cd ga4-dashboard
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up your Google OAuth 2.0 credentials:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the Google Analytics Data API and Google Analytics Admin API
   - Create OAuth 2.0 credentials (Web application type)
   - Set the authorized redirect URI to `http://localhost:5000/oauth2callback`
   - Download the credentials JSON file

5. Configure the application:
   - Create a `.env` file in the project root with the following content:
     ```
     FLASK_ENV=development
     SECRET_KEY=your-secret-key
     GOOGLE_CLIENT_ID=your-client-id
     GOOGLE_CLIENT_SECRET=your-client-secret
     ```

6. Initialize the database:
   ```
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

7. Run the application:
   ```
   flask run
   ```

8. Open your browser and navigate to `http://localhost:5000`

## Usage

1. **Login**: Sign in with your Google account that has access to GA4 properties
2. **Dashboard**: View an overview of your GA4 properties and key metrics
3. **Properties**: Manage your GA4 properties and sync them with Google Analytics
4. **Reports**: Generate various types of reports with customizable parameters
5. **Selection Sets**: Create and manage property selection sets for easier reporting
6. **Settings**: Configure application settings

## Project Structure

```
ga4-dashboard/
├── app.py                  # Main application file
├── config.py               # Configuration settings
├── modules/                # Application modules
│   ├── auth.py             # Authentication module
│   ├── ga_api.py           # Google Analytics API integration
│   ├── models.py           # Database models
│   ├── ga4_metadata_service.py  # GA4 metadata service
│   └── reporting/          # Reporting modules
│       ├── common.py       # Common reporting functions
│       ├── url_analytics.py  # URL analytics reporting
│       ├── property_aggregation.py  # Property aggregation reporting
│       └── common_pdf.py   # PDF generation
├── static/                 # Static files
│   ├── css/                # CSS files
│   ├── js/                 # JavaScript files
│   └── img/                # Image files
└── templates/              # HTML templates
    ├── base.html           # Base template
    ├── dashboard.html      # Dashboard page
    ├── login.html          # Login page
    ├── properties.html     # Properties management page
    ├── reports.html        # Reports page
    ├── selection_sets.html # Selection sets page
    ├── settings.html       # Settings page
    ├── errors/             # Error pages
    └── reports/            # Report templates
        ├── url_analytics.html  # URL analytics report
        ├── property_aggregation.html  # Property aggregation report
        └── pdf/            # PDF templates
```

## Requirements

See [requirements.txt](requirements.txt) for a complete list of dependencies.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [Google Analytics Data API](https://developers.google.com/analytics/devguides/reporting/data/v1)
- [Flask](https://flask.palletsprojects.com/)
- [Chart.js](https://www.chartjs.org/)
- [Tailwind CSS](https://tailwindcss.com/)