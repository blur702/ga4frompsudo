# Google Analytics 4 Dashboard: API Integration

## Google Analytics 4 API

The application integrates with two primary Google Analytics 4 APIs:

1. **Google Analytics Data API v1beta** - For retrieving analytics data
2. **Google Analytics Admin API** - For managing GA4 properties and account information

### Google Analytics Data API

The Google Analytics Data API v1beta provides access to Google Analytics 4 (GA4) report data. The application uses this API to retrieve metrics and dimensions for various reports.

**Key Endpoints Used:**

| Endpoint | Purpose | Implementation |
|----------|---------|----------------|
| `runReport` | Retrieve report data for a single property | `get_analytics_report()` in `ga_api.py` |
| `batchRunReports` | Retrieve report data for multiple properties | Not directly implemented, but simulated through multiple calls |
| `getMetadata` | Retrieve metadata about available metrics and dimensions | `update_ga4_metadata()` in `ga4_metadata_service.py` |

**Authentication:**

Authentication is handled through OAuth 2.0 using the following scopes:
- `https://www.googleapis.com/auth/analytics.readonly`
- `https://www.googleapis.com/auth/analytics`

The authentication flow is implemented in the `auth.py` module, with the `build_credentials()` function providing the necessary credentials for API calls.

**Request Format:**

A typical request to the `runReport` endpoint is structured as follows:

```python
request = RunReportRequest(
    property=ga_property_id,
    dimensions=[Dimension(name="date"), Dimension(name="browser")],
    metrics=[Metric(name="activeUsers"), Metric(name="sessions")],
    date_ranges=[DateRange(start_date="2023-01-01", end_date="2023-01-31")]
)
```

**Response Format:**

The response from the GA4 Data API is a structured protocol buffer that is converted to JSON for storage and processing. A typical response structure includes:

```json
{
  "dimensionHeaders": [
    {"name": "date"},
    {"name": "browser"}
  ],
  "metricHeaders": [
    {"name": "activeUsers", "type": "TYPE_INTEGER"},
    {"name": "sessions", "type": "TYPE_INTEGER"}
  ],
  "rows": [
    {
      "dimensionValues": [
        {"value": "20230101"},
        {"value": "Chrome"}
      ],
      "metricValues": [
        {"value": "1234"},
        {"value": "5678"}
      ]
    }
  ]
}
```

**Error Handling:**

The application implements comprehensive error handling for GA4 API calls, including:
- Timeout handling with concurrent.futures
- Specific error messages for common API errors
- Fallback mechanisms when API calls fail
- Rate limiting detection and handling

### Google Analytics Admin API

The Google Analytics Admin API is used to retrieve information about GA4 properties, accounts, and data streams.

**Key Endpoints Used:**

| Endpoint | Purpose | Implementation |
|----------|---------|----------------|
| `listAccountSummaries` | List all GA4 accounts and properties | `list_ga4_properties()` in `ga_api.py` |
| `listDataStreams` | List data streams for a property | Used within `list_ga4_properties()` to get website URLs |

**Authentication:**

Authentication uses the same OAuth 2.0 flow as the Data API, with credentials provided by the `build_credentials()` function.

## Internal Module APIs

### GA API Module (`ga_api.py`)

**Key Functions:**

| Function | Purpose | Parameters | Return Value |
|----------|---------|------------|--------------|
| `get_admin_service()` | Get an authenticated Admin API client | None | `AnalyticsAdminServiceClient` or None |
| `get_data_service()` | Get an authenticated Data API client | None | `BetaAnalyticsDataClient` or None |
| `list_ga4_properties()` | List all GA4 properties | None | List of property dictionaries |
| `get_analytics_report()` | Fetch analytics data | property_id, start_date, end_date, dimensions, metrics | JSON string of report data |
| `fetch_and_store_analytics_report()` | Fetch and store analytics data | property_id, start_date, end_date, dimensions, metrics | AnalyticsData object |
| `batch_fetch_analytics_data()` | Fetch data for multiple properties | start_date, end_date, dimensions, metrics, property_ids | List of AnalyticsData objects |
| `validate_metrics_and_dimensions()` | Validate metrics and dimensions | metrics, dimensions | Tuple of valid metrics and dimensions |
| `get_analytics_report_with_dimension_batching()` | Fetch report with dimension batching | property_id, start_date, end_date, dimensions, metrics | JSON string of combined report data |
| `join_analytics_results()` | Join results from multiple dimension batches | results, common_dimensions | JSON string of combined results |

### Reporting Modules

**Common Reporting Module (`reporting/common.py`):**

| Function | Purpose | Parameters | Return Value |
|----------|---------|------------|--------------|
| `extract_metric_values()` | Extract metric values from report data | report_data, metric_name | List of metric values |
| `extract_dimension_values()` | Extract dimension values from report data | report_data, dimension_name | List of dimension values |
| `get_date_range_for_form()` | Get date range for form | days_ago | Tuple of start_date, end_date |
| `format_date_for_display()` | Format date for display | date_obj | Formatted date string |
| `calculate_percentage()` | Calculate percentage | part, whole | Percentage value |

**URL Analytics Module (`reporting/url_analytics.py`):**

| Function | Purpose | Parameters | Return Value |
|----------|---------|------------|--------------|
| `generate_url_analytics_report()` | Generate URL analytics report | url, start_date, end_date, metrics, dimensions | Report data dictionary |
| `get_url_path_from_full_url()` | Extract path from URL | url | URL path string |
| `validate_url()` | Validate URL format | url | Boolean |

**Property Aggregation Module (`reporting/property_aggregation.py`):**

| Function | Purpose | Parameters | Return Value |
|----------|---------|------------|--------------|
| `generate_property_aggregation_report()` | Generate property aggregation report | property_ids, start_date, end_date, metrics, dimensions | Report data dictionary |
| `aggregate_metrics_across_properties()` | Aggregate metrics across properties | property_reports, metrics | Dictionary of aggregated metrics |

**PDF Generation Module (`reporting/common_pdf.py`):**

| Function | Purpose | Parameters | Return Value |
|----------|---------|------------|--------------|
| `generate_report_pdf()` | Generate PDF for any report | report_data, template_name, output_path, title, include_summary, include_url_overview, first_url_only, include_screenshot | Path to generated PDF |
| `generate_report_summary()` | Generate text summary of report | report_data, report_type | Summary text |
| `generate_url_overview()` | Generate overview of URLs in report | report_data, first_only | URL overview text |
| `take_url_screenshot()` | Take screenshot of URL | url, output_dir | Path to screenshot |

## API Best Practices

### GA4 API Best Practices

1. **Dimension Batching**: The application implements dimension batching to optimize API calls when requesting multiple dimensions.
2. **Metric Aggregation**: Different metrics require different aggregation methods (sum, average, unique) when combining results.
3. **Rate Limiting**: The application handles rate limiting by implementing timeouts and retries.
4. **Caching**: Analytics data is cached in the database to reduce API calls.

### Internal API Best Practices

1. **Error Handling**: All API functions include comprehensive error handling.
2. **Logging**: Detailed logging is implemented for debugging and monitoring.
3. **Parameter Validation**: Input parameters are validated before use.
4. **Consistent Return Values**: Functions return consistent data structures or None on error.

## API Limitations

### GA4 API Limitations

1. **Request Quotas**: The GA4 API has daily and per-minute request quotas.
2. **Sampling**: Large data sets may be sampled by the GA4 API.
3. **Data Freshness**: Real-time data may have a delay of several minutes.
4. **Dimension Combinations**: Not all dimension combinations are valid.
5. **Maximum Dimensions**: The GA4 API limits dimensions to 9 per request, requiring dimension batching for reports with many dimensions.

### Performance Considerations

1. **Dimension Batching**: Using too many dimensions in a single request can cause performance issues.
2. **Date Range**: Large date ranges can result in slower responses and sampling.
3. **Property Count**: Fetching data for many properties simultaneously can be slow.
4. **API Rate Limits**: The application must stay within API rate limits to avoid throttling.