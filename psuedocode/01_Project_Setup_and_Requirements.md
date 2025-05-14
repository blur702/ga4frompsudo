# 01 - Project Setup and Requirements

This document outlines the initial project directory structure and the Python package dependencies required for the GA4 Analytics Dashboard.

## 1. Directory Structure (from `mvc-architecture.md` and `app-initialization-pseudocode.md`)

Create the following initial directory structure for the project:

ga4_dashboard/
├── app/
│ ├── models/
│ ├── views/
│ │ ├── templates/
│ │ │ └── components/
│ │ └── static/
│ │ ├── css/
│ │ ├── js/
│ │ │ └── components/
│ │ └── images/
│ ├── controllers/
│ ├── services/
│ ├── plugins/
│ │ ├── traffic_analysis/
│ │ ├── engagement_metrics/
│ │ └── conversion_tracking/
│ ├── utils/
│ ├── init.py # To be implemented (Application factory)
│ └── config.py # To be implemented (Configuration)
├── tests/
│ ├── unit/
│ │ ├── models/
│ │ ├── services/
│ │ ├── controllers/
│ │ ├── plugins/
│ │ └── utils/
│ ├── integration/
│ ├── e2e/
│ └── conftest.py # To be implemented (Test configuration)
├── migrations/ # For database migrations (if needed later)
├── requirements.txt # Defined below
├── run.py # To be implemented (Application entry point)
└── README.md

## 2. Dependencies (`requirements.txt`)

Create a `requirements.txt` file in the root of the `ga4_dashboard` directory with the following content. This was specified in `app-initialization-pseudocode.md`.

```txt
# Flask
Flask==2.0.1
Werkzeug==2.0.1
Jinja2==3.0.1
MarkupSafe==2.0.1
itsdangerous==2.0.1
click==8.0.1

# Google API
google-api-python-client==2.15.0
google-auth==2.0.0
google-auth-httplib2==0.1.0
google-auth-oauthlib==0.4.5

# Database
# SQLite3 is part of the Python standard library.

# Security
cryptography==35.0.0
PyJWT==2.1.0

# PDF Generation
reportlab==3.6.1

# Date and Time
python-dateutil==2.8.2

# Testing
pytest==6.2.5
pytest-flask==1.2.0
coverage==5.5
# selenium==4.x.x # If using Selenium for E2E tests

# Development
python-dotenv==0.19.0
```
