# Google Analytics 4 Dashboard: System Architecture

## High-Level Architecture

The GA4 Dashboard follows a modular architecture with clear separation of concerns between components. The application is built using the Flask web framework and integrates with the Google Analytics 4 API for data retrieval.

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  User Browser   │◄───►│  Flask Web App  │◄───►│  Google         │
│                 │     │                 │     │  Analytics 4    │
└─────────────────┘     └────────┬────────┘     │  API            │
                                 │              │                 │
                                 │              └─────────────────┘
                                 ▼
                        ┌─────────────────┐
                        │                 │
                        │  SQLite/SQL     │
                        │  Database       │
                        │                 │
                        └─────────────────┘
```

The architecture consists of four main components:
1. **User Browser**: The client-side interface accessed by users
2. **Flask Web App**: The server-side application handling requests and business logic
3. **Google Analytics 4 API**: External API providing analytics data
4. **SQLite/SQL Database**: Data storage for properties, analytics data, and application settings

## Component Architecture

The application is organized into the following key components:

```
┌─────────────────────────────────────────────────────────────────┐
│                         Flask Application                        │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │
│  │             │  │             │  │             │  │         │ │
│  │ Auth Module │  │ GA4 API     │  │ Reporting   │  │ PDF     │ │
│  │             │  │ Integration │  │ Modules     │  │ Module  │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘ │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                      Database Models                         ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

1. **Authentication Module** (`modules/auth.py`):
   - Implements OAuth 2.0 flow with Google
   - Manages user sessions
   - Stores and refreshes access tokens
   - Provides login protection via decorators

2. **GA4 API Integration** (`modules/ga_api.py`):
   - Fetches GA4 properties accessible to the user
   - Retrieves analytics data with proper dimension batching
   - Validates metrics and dimensions
   - Handles API errors and rate limiting
   - Stores analytics data in the database

3. **Reporting Modules** (`modules/reporting/`):
   - Process and visualize analytics data for different report types
   - Each report type has its own dedicated module
   - Implement data aggregation and transformation
   - Generate visualizations and tables

4. **PDF Generation** (`modules/reporting/common_pdf.py`):
   - Converts HTML reports to PDF
   - Adds executive summaries
   - Takes screenshots of URLs
   - Generates URL overviews

5. **Database Models** (`modules/models.py`):
   - Define the structure of the application's data storage
   - Use SQLAlchemy ORM for database interactions
   - Implement relationships between models
   - Provide data access methods

## Process Flows

### Authentication Flow

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│          │    │          │    │          │    │          │    │          │
│  User    │───►│  Login   │───►│  Google  │───►│  OAuth   │───►│  Session │
│  Browser │    │  Page    │    │  Auth    │    │  Callback│    │  Storage │
│          │    │          │    │          │    │          │    │          │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
```

1. User navigates to the application and is redirected to the login page
2. User clicks the Google sign-in button
3. User is redirected to Google's authentication page
4. User grants permission to the application
5. Google redirects back to the application's OAuth callback URL
6. Application verifies the authentication and stores credentials in the session
7. User is redirected to the main dashboard

### Data Retrieval Flow

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│          │    │          │    │          │    │          │    │          │
│  User    │───►│  Request │───►│  GA4 API │───►│  Process │───►│  Store   │
│  Browser │    │  Data    │    │  Client  │    │  Data    │    │  Data    │
│          │    │          │    │          │    │          │    │          │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
```

1. User selects properties and date range for data retrieval
2. Application creates a request to the GA4 API
3. Application batches dimensions to optimize API calls
4. GA4 API returns data for each batch
5. Application processes and joins the results
6. Data is stored in the database for future use

### Report Generation Flow

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│          │    │          │    │          │    │          │    │          │
│  User    │───►│  Select  │───►│  Generate│───►│  Display │───►│  Download│
│  Browser │    │  Report  │    │  Report  │    │  Report  │    │  PDF     │
│          │    │  Type    │    │          │    │          │    │          │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
```

1. User selects a report type and configures parameters
2. Application retrieves necessary data from the database
3. Reporting module processes the data and generates visualizations
4. Report is displayed in the browser
5. User can download the report as a PDF

### PDF Generation Flow

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│          │    │          │    │          │    │          │    │          │
│  Request │───►│  Generate│───►│  Take    │───►│  Render  │───►│  Convert │
│  PDF     │    │  Summary │    │  Screen- │    │  Template│    │  to PDF  │
│          │    │          │    │  shots   │    │          │    │          │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
```

1. User requests a PDF version of a report
2. Application generates an executive summary
3. Application takes screenshots of URLs (if applicable)
4. Application renders the PDF template with the report data
5. Template is converted to PDF using Playwright or pdfkit
6. PDF is sent to the user's browser for download

## Technology Stack

### Backend
- **Python**: Primary programming language
- **Flask**: Web framework
- **SQLAlchemy**: ORM for database interactions
- **Google API Client**: For interacting with Google Analytics API
- **Playwright/pdfkit**: For PDF generation and website thumbnail presentation

### Frontend
- **HTML/CSS**: For page structure and styling
- **JavaScript**: For interactive elements
- **Tailwind**: CSS framework for responsive design
- **Chart.js**: For data visualization

### Database
- **SQLite**: Default database for development
- **SQL Database**: Configurable for production (MySQL, PostgreSQL, MariaDB)
- **Database Migration**: Provide a migration method to move data between SQLite and MySQL/MariaDB/PostgreSQL

### External Services
- **Google Analytics 4 API**: For retrieving analytics data
- **Google OAuth 2.0**: For authentication