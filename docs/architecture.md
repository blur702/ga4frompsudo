# Architecture

The GA4 Analytics Dashboard follows the Model-View-Controller (MVC) architecture pattern with additional components like services and plugins for enhanced functionality.

## MVC Architecture Overview

### Model Layer
- **Purpose**: Data storage, manipulation, and business logic
- **Components**: Database interactions, GA4 API client, data processing
- **Location**: `/app/models/` directory
- **Key Models**:
  - `BaseModel`: Abstract base class providing common database operations
  - `Property`: Represents GA4 properties
  - `Website`: Represents websites associated with properties
  - `Report`: Represents generated reports
  - `ReportData`: Represents report data points

### View Layer
- **Purpose**: User interface presentation
- **Components**: Templates, frontend JavaScript, CSS
- **Location**: `/app/views/` and `/app/static/` directories
- **Template Structure**:
  - Base template with common layout elements
  - Partials for reusable components (navigation, footer, etc.)
  - Page-specific templates

### Controller Layer
- **Purpose**: Handle user requests, coordinate model and view
- **Components**: Route handlers, request processing, response formatting
- **Location**: `/app/controllers/` directory
- **Key Controllers**:
  - `auth_routes`: Authentication-related routes
  - `dashboard_routes`: Main dashboard views
  - `reports_routes`: Report generation and display
  - `admin_routes`: Administrative functions
  - `api_routes`: API endpoints

## Additional Components

### Services
- **Purpose**: Encapsulate complex business logic and operations
- **Components**: Report generation, authentication, security
- **Location**: `/app/services/` directory
- **Key Services**:
  - `AuthService`: Handles authentication with GA4 API
  - `GA4Service`: Manages interaction with Google Analytics 4 API
  - `PluginService`: Manages plugin registration and execution
  - `ReportService`: Handles report generation and storage
  - `SecurityService`: Provides security features

### Plugins
- **Purpose**: Modular, extensible functionality for analytics processing
- **Components**: Traffic analysis, engagement metrics, conversion tracking
- **Location**: `/app/plugins/` directory
- **Plugin Architecture**:
  - `BasePlugin`: Abstract base class for all plugins
  - Specific plugin implementations that inherit from BasePlugin

### Utilities
- **Purpose**: Helper functions and common utilities
- **Components**: Date formatting, security helpers, accessibility
- **Location**: `/app/utils/` directory

## Application Flow

1. User sends a request to a specific route
2. A controller handles the request
3. The controller interacts with models and services as needed
4. Services may utilize plugins for data processing
5. The controller renders a view template with the processed data
6. The view is returned to the user

## Database Schema

The application uses SQLite as its database, with the following tables:
- `properties`: GA4 properties information
- `websites`: Website information associated with properties
- `reports`: Report metadata
- `report_data`: Report data points

## Authentication Flow

The application uses OAuth 2.0 for authentication with the Google Analytics API:
1. User initiates authentication
2. User is redirected to Google for authorization
3. Upon approval, Google redirects back with an authorization code
4. The application exchanges the code for access and refresh tokens
5. Tokens are securely stored for future API access