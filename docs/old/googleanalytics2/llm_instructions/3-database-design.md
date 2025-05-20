# Google Analytics 4 Dashboard: Database Design

## Entity-Relationship Diagram

```
┌─────────────┐       ┌───────────────┐       ┌─────────────────────┐
│ Property    │       │ AnalyticsData │       │ StructuredMetric    │
├─────────────┤       ├───────────────┤       ├─────────────────────┤
│ id          │◄──┐   │ id            │◄──┐   │ id                  │
│ ga_property_│   │   │ property_id   │───┘   │ analytics_data_id   │───┐
│ display_name│   │   │ timestamp     │       │ property_id         │───┤
│ website_url │   │   │ report_start_ │       │ metric_id           │───┤
│ exclude_from│   │   │ report_end_   │       │ date                │   │
│ last_synced │   │   │ raw_data_json │       │ value               │   │
└─────────────┘   │   └───────────────┘       │ dimensions_json     │   │
                  │                           └─────────────────────┘   │
                  │                                                     │
                  │   ┌───────────────┐                                │
                  └───┤ PropertySelec │                                │
                      ├───────────────┤                                │
                      │ id            │                                │
                      │ name          │                                │
                      │ description   │                                │
                      │ property_ids  │                                │
                      │ created_at    │                                │
                      │ updated_at    │                                │
                      └───────────────┘                                │
                                                                       │
┌─────────────┐       ┌───────────────┐                                │
│ Setting     │       │ ReportTemplate│                                │
├─────────────┤       ├───────────────┤                                │
│ id          │       │ id            │                                │
│ key         │       │ name          │                                │
│ value       │       │ metrics       │                                │
│ description │       │ dimensions    │                                │
│ updated_at  │       │ url_type      │                                │
└─────────────┘       │ saved_urls    │                                │
                      │ created_at    │                                │
                      │ updated_at    │                                │
                      └───────────────┘                                │
                                                                       │
┌─────────────┐       ┌───────────────┐       ┌─────────────────────┐ │
│ MetricDefin │       │ DimensionDefi │       │ DimensionValue      │ │
├─────────────┤       ├───────────────┤       ├─────────────────────┤ │
│ id          │◄──────│ id            │◄──────│ id                  │ │
│ api_name    │       │ api_name      │       │ dimension_id        │ │
│ display_name│       │ display_name  │       │ api_value           │ │
│ description │       │ description   │       │ display_value       │ │
│ category    │       │ category      │       └─────────────────────┘ │
│ aggregation_│       │ is_custom     │                               │
│ is_custom   │       │ is_deprecated │                               │
│ is_deprecate│       │ last_updated  │                               │
│ last_updated│◄──────┘               │                               │
└─────────────┘                                                       │
      ▲                                                               │
      │                                                               │
      └───────────────────────────────────────────────────────────────┘
```

## Table Definitions

### Property

The `Property` table stores information about Google Analytics 4 properties.

| Column | Type | Description | Constraints |
|--------|------|-------------|------------|
| id | Integer | Primary key | PRIMARY KEY |
| ga_property_id | String(80) | Google Analytics property ID | NOT NULL, UNIQUE |
| display_name | String(120) | Human-readable name of the property | NOT NULL |
| website_url | String(255) | URL of the website associated with the property | NULL |
| exclude_from_global_reports | Boolean | Whether to exclude this property from global reports | NOT NULL, DEFAULT FALSE |
| last_synced | DateTime | Timestamp of when the property was last synchronized | DEFAULT current timestamp |

**Relationships:**
- One-to-many relationship with `AnalyticsData`
- One-to-many relationship with `StructuredMetric`

### AnalyticsData

The `AnalyticsData` table stores raw analytics data fetched from Google Analytics.

| Column | Type | Description | Constraints |
|--------|------|-------------|------------|
| id | Integer | Primary key | PRIMARY KEY |
| property_id | Integer | Foreign key referencing the Property model | NOT NULL, FOREIGN KEY |
| timestamp | DateTime | When the data was fetched from Google Analytics | DEFAULT current timestamp, INDEX |
| report_start_date | Date | Start date of the analytics report | NOT NULL |
| report_end_date | Date | End date of the analytics report | NOT NULL |
| raw_data_json | Text | Raw JSON data returned by the Google Analytics API | NULL |

**Relationships:**
- Many-to-one relationship with `Property`
- One-to-many relationship with `StructuredMetric`

### Setting

The `Setting` table stores application settings as key-value pairs.

| Column | Type | Description | Constraints |
|--------|------|-------------|------------|
| id | Integer | Primary key | PRIMARY KEY |
| key | String(50) | The setting key (e.g., "gemini_api_key") | NOT NULL, UNIQUE |
| value | Text | The setting value | NULL |
| description | String(255) | A description of the setting | NULL |
| updated_at | DateTime | Timestamp of when the setting was last updated | DEFAULT current timestamp, ON UPDATE current timestamp |

### PropertySelectionSet

The `PropertySelectionSet` table allows users to save and reuse selections of properties for generating reports.

| Column | Type | Description | Constraints |
|--------|------|-------------|------------|
| id | Integer | Primary key | PRIMARY KEY |
| name | String(100) | The name of the selection set | NOT NULL, UNIQUE |
| description | String(255) | A description of the selection set | NULL |
| property_ids | Text | JSON list of Property.id values | NOT NULL |
| created_at | DateTime | Timestamp of when the selection set was created | DEFAULT current timestamp |
| updated_at | DateTime | Timestamp of when the selection set was last updated | DEFAULT current timestamp, ON UPDATE current timestamp |

### ReportTemplate

The `ReportTemplate` table allows users to save and reuse report templates with specific metrics, dimensions, and URL configurations.

| Column | Type | Description | Constraints |
|--------|------|-------------|------------|
| id | Integer | Primary key | PRIMARY KEY |
| name | String(100) | The name of the report template | NOT NULL, UNIQUE |
| metrics | Text | JSON list of selected metric names | NOT NULL |
| dimensions | Text | JSON list of selected dimension names | NOT NULL |
| url_type | String(20) | Type of URL configuration ('single' or 'multiple') | NOT NULL |
| saved_urls | Text | JSON list of saved URLs | NULL |
| created_at | DateTime | Timestamp of when the template was created | DEFAULT current timestamp |
| updated_at | DateTime | Timestamp of when the template was last updated | DEFAULT current timestamp, ON UPDATE current timestamp |

### MetricDefinition

The `MetricDefinition` table stores metadata about GA4 metrics.

| Column | Type | Description | Constraints |
|--------|------|-------------|------------|
| id | Integer | Primary key | PRIMARY KEY |
| api_name | String(100) | The API name of the metric (e.g., "activeUsers") | NOT NULL, UNIQUE |
| display_name | String(100) | The human-readable name of the metric | NOT NULL |
| description | Text | A description of the metric | NULL |
| category | String(50) | The category of the metric (e.g., "User", "Session") | NULL |
| aggregation_type | String(20) | How the metric should be aggregated (sum, average, unique) | NOT NULL, DEFAULT "sum" |
| is_custom | Boolean | Whether this is a custom metric | NOT NULL, DEFAULT FALSE |
| is_deprecated | Boolean | Whether this metric is deprecated | NOT NULL, DEFAULT FALSE |
| last_updated | DateTime | When this definition was last updated | DEFAULT current timestamp, ON UPDATE current timestamp |

**Relationships:**
- One-to-many relationship with `StructuredMetric`

### DimensionDefinition

The `DimensionDefinition` table stores metadata about GA4 dimensions.

| Column | Type | Description | Constraints |
|--------|------|-------------|------------|
| id | Integer | Primary key | PRIMARY KEY |
| api_name | String(100) | The API name of the dimension (e.g., "date") | NOT NULL, UNIQUE |
| display_name | String(100) | The human-readable name of the dimension | NOT NULL |
| description | Text | A description of the dimension | NULL |
| category | String(50) | The category of the dimension (e.g., "Time", "Geography") | NULL |
| is_custom | Boolean | Whether this is a custom dimension | NOT NULL, DEFAULT FALSE |
| is_deprecated | Boolean | Whether this dimension is deprecated | NOT NULL, DEFAULT FALSE |
| last_updated | DateTime | When this definition was last updated | DEFAULT current timestamp, ON UPDATE current timestamp |

**Relationships:**
- One-to-many relationship with `DimensionValue`

### StructuredMetric

The `StructuredMetric` table stores structured metrics data extracted from the raw GA4 API response.

| Column | Type | Description | Constraints |
|--------|------|-------------|------------|
| id | Integer | Primary key | PRIMARY KEY |
| analytics_data_id | Integer | Foreign key referencing the AnalyticsData model | NOT NULL, FOREIGN KEY |
| property_id | Integer | Foreign key referencing the Property model | NOT NULL, FOREIGN KEY |
| metric_id | Integer | Foreign key referencing the MetricDefinition model | NOT NULL, FOREIGN KEY |
| date | Date | The date of the metric data | NOT NULL, INDEX |
| value | Float | The numeric value of the metric | NOT NULL |
| dimensions_json | Text | JSON string of dimension key-value pairs | NULL |
| created_at | DateTime | Timestamp of when the record was created | DEFAULT current timestamp |

**Relationships:**
- Many-to-one relationship with `AnalyticsData`
- Many-to-one relationship with `Property`
- Many-to-one relationship with `MetricDefinition`

## Data Flow

### Analytics Data Flow

1. User selects GA4 properties to analyze
2. Application fetches raw analytics data from GA4 API
3. Raw data is stored in the `AnalyticsData` table
4. Structured metrics are extracted and stored in the `StructuredMetric` table
5. Reports are generated using data from both raw and structured tables

### Metadata Flow

1. Application fetches metadata about metrics and dimensions from GA4 API
2. Metadata is stored in `MetricDefinition` and `DimensionDefinition` tables
3. Metadata is used for validation and proper aggregation of metrics

## Database Optimization

### Indexes

The following indexes are defined to optimize query performance:

- `AnalyticsData.timestamp` - For efficient querying of analytics data by time
- `AnalyticsData.property_id` - For efficient joining with Property table
- `StructuredMetric.date` - For efficient querying of metrics by date
- `StructuredMetric.property_id` - For efficient filtering by property
- `StructuredMetric.metric_id` - For efficient filtering by metric

### Query Optimization

The application implements several query optimization techniques:

1. **Selective Data Retrieval**: Only necessary data is retrieved from the database
2. **Efficient Joins**: Joins are optimized to minimize data transfer
3. **Caching**: Frequently accessed data is cached to reduce database load
4. **Batch Processing**: Data is processed in batches to reduce memory usage