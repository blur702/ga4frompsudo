# Database Models

This document describes the database models used in the GA4 Analytics Dashboard application. The application uses SQLite for data storage with a flexible schema to accommodate different types of analytics data.

## Database Structure

The database consists of the following tables:
- `properties`: GA4 properties information
- `websites`: Website information associated with properties
- `reports`: Report metadata
- `report_data`: Report data points

## Base Model

The `BaseModel` class serves as the foundation for all other models. It provides common functionality for database operations:

- `save()`: Saves the model instance to the database (INSERT or UPDATE)
- `delete()`: Deletes the model instance from the database
- `find_by_id()`: Finds a record by its primary key
- `find_all()`: Retrieves all records with optional filtering and pagination

All model classes inherit from this base class and implement the following abstract methods:
- `TABLE_NAME`: Property returning the name of the database table
- `_to_dict()`: Converts model attributes to a dictionary for database operations
- `_from_db_row()`: Creates a model instance from a database row

## Property Model

The `Property` model represents a Google Analytics 4 property.

### Schema

```sql
CREATE TABLE IF NOT EXISTS properties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id TEXT UNIQUE NOT NULL, -- GA4 property ID
    property_name TEXT,
    account_id TEXT,
    create_time TEXT, -- ISO 8601 format
    update_time TEXT  -- ISO 8601 format
);
```

### Attributes

- `id`: Database primary key
- `property_id`: Google Analytics 4 property ID (e.g., "123456789")
- `property_name`: Human-readable name of the property
- `account_id`: Google Analytics account ID associated with the property
- `create_time`: When the property was created (ISO 8601 format)
- `update_time`: When the property was last updated (ISO 8601 format)

## Website Model

The `Website` model represents a website associated with a GA4 property.

### Schema

```sql
CREATE TABLE IF NOT EXISTS websites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    website_id TEXT UNIQUE NOT NULL, -- Could be GA4 stream ID
    property_db_id INTEGER NOT NULL, -- Foreign key to properties.id
    website_url TEXT,
    create_time TEXT, -- ISO 8601 format
    update_time TEXT, -- ISO 8601 format
    FOREIGN KEY (property_db_id) REFERENCES properties (id) ON DELETE CASCADE
);
```

### Attributes

- `id`: Database primary key
- `website_id`: Identifier for the website (typically GA4 stream ID)
- `property_db_id`: Foreign key to the properties table
- `website_url`: URL of the website
- `create_time`: When the website record was created (ISO 8601 format)
- `update_time`: When the website record was last updated (ISO 8601 format)

## Report Model

The `Report` model represents a generated analytics report.

### Schema

```sql
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_name TEXT NOT NULL,
    report_type TEXT NOT NULL, -- e.g., 'traffic_analysis', 'engagement'
    parameters TEXT,           -- JSON string of parameters used for generation
    create_time TEXT NOT NULL, -- ISO 8601 format
    status TEXT,               -- e.g., 'pending', 'generating', 'completed', 'failed'
    file_path TEXT             -- Path to the generated report file if applicable
);
```

### Attributes

- `id`: Database primary key
- `report_name`: User-friendly name of the report
- `report_type`: Type of report (e.g., 'traffic_analysis', 'engagement')
- `parameters`: JSON string containing parameters used to generate the report
- `create_time`: When the report was created (ISO 8601 format)
- `status`: Current status of the report ('pending', 'generating', 'completed', 'failed')
- `file_path`: Path to the generated report file (if applicable)

## Report Data Model

The `ReportData` model represents individual data points in a report.

### Schema

```sql
CREATE TABLE IF NOT EXISTS report_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_db_id INTEGER NOT NULL,      -- Foreign key to reports.id
    property_ga4_id TEXT,               -- GA4 Property ID this data pertains to
    metric_name TEXT NOT NULL,
    metric_value TEXT,                  -- Store as TEXT for flexibility, convert on read
    dimension_name TEXT,
    dimension_value TEXT,
    data_date TEXT,                     -- Date for which this data point is relevant (YYYY-MM-DD)
    timestamp TEXT NOT NULL,            -- When this record was saved (ISO 8601)
    FOREIGN KEY (report_db_id) REFERENCES reports (id) ON DELETE CASCADE
);
```

### Attributes

- `id`: Database primary key
- `report_db_id`: Foreign key to the reports table
- `property_ga4_id`: Google Analytics 4 property ID this data pertains to
- `metric_name`: Name of the metric (e.g., 'pageviews', 'sessions')
- `metric_value`: Value of the metric (stored as text for flexibility)
- `dimension_name`: Name of the dimension (e.g., 'date', 'deviceCategory')
- `dimension_value`: Value of the dimension
- `data_date`: Date for which this data point is relevant (YYYY-MM-DD)
- `timestamp`: When this record was saved (ISO 8601 format)

## Relationships

- A Property can have multiple Websites (one-to-many)
- A Report can have multiple ReportData entries (one-to-many)
- ReportData is associated with a Report (many-to-one)

## Additional Notes

- The application uses ISO 8601 format for all datetime fields (e.g., '2023-06-15T14:30:00+00:00')
- For numeric values in the `report_data` table, the values are stored as text and converted to the appropriate type when read
- The database schema is designed to be flexible to accommodate various types of analytics data