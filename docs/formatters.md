# Formatters Usage Guide

## Overview

The GA4 Analytics Dashboard includes a comprehensive set of formatting utilities to ensure consistent display of numbers, dates, percentages, and other data types throughout the application. This document outlines the available formatters and how to use them.

## Available Formatters

### Number Formatting

```python
from app.utils import format_number

# Basic formatting with thousands separators
format_number(1234)  # "1,234"

# With decimal precision
format_number(1234.56, precision=2)  # "1,234.56"

# With abbreviation for large numbers
format_number(1234567, abbreviate=True)  # "1.2M"
```

In templates:

```html
{{ value|format_number }}
{{ value|format_number(precision=2) }}
{{ value|format_number(abbreviate=True) }}
```

### Percentage Formatting

```python
from app.utils import format_percentage

# Format decimal as percentage
format_percentage(0.75)  # "75.00%"

# Custom precision
format_percentage(0.75, precision=0)  # "75%"

# Without percentage sign
format_percentage(0.75, include_sign=False)  # "75.00"
```

In templates:

```html
{{ value|format_percentage }}
{{ value|format_percentage(precision=0) }}
```

### Date Formatting

```python
from app.utils import format_date
import datetime

# Format date object
date_obj = datetime.date(2023, 9, 15)
format_date(date_obj)  # "2023-09-15"
format_date(date_obj, format_str="%B %d, %Y")  # "September 15, 2023"

# Format string dates
format_date("2023-09-15", format_str="%d/%m/%Y")  # "15/09/2023"
format_date("20230915", format_str="%d/%m/%Y")  # "15/09/2023"
```

In templates:

```html
{{ value|format_date }}
{{ value|format_date(format_str="%B %d, %Y") }}
```

### Duration Formatting

```python
from app.utils import format_duration

# Human-readable format
format_duration(3665)  # "1h 1m 5s"

# Clock format
format_duration(3665, format_type='clock')  # "01:01:05"

# Compact format
format_duration(3665, format_type='compact')  # "1h1m5s"
```

In templates:

```html
{{ seconds|format_duration }}
{{ seconds|format_duration(format_type='clock') }}
```

### File Size Formatting

```python
from app.utils import format_file_size

format_file_size(1024)  # "1.00 KB"
format_file_size(1536, precision=1)  # "1.5 KB"
format_file_size(1024 * 1024)  # "1.00 MB"
```

In templates:

```html
{{ bytes|format_file_size }}
{{ bytes|format_file_size(precision=1) }}
```

### Metric Name Formatting

```python
from app.utils import format_metric_name

# Format camelCase
format_metric_name("screenPageViews")  # "Screen Page Views"

# Format snake_case
format_metric_name("avg_session_duration")  # "Avg Session Duration"
```

In templates:

```html
{{ metric_name|format_metric_name }}
```

### Data Conversion

```python
from app.utils import data_to_csv, data_to_json

# Convert to CSV
data = [{'name': 'John', 'age': 30}, {'name': 'Alice', 'age': 25}]
csv_string = data_to_csv(data)

# Convert to JSON
json_string = data_to_json(data, pretty=True)
```

### GA4 Specific Formatters

```python
from app.utils import format_dimension_value, format_ga4_report_data

# Format dimension values appropriately
format_dimension_value('date', '20230915')  # "Sep 15, 2023"
format_dimension_value('deviceCategory', 'mobile')  # "Mobile"

# Format entire GA4 report
formatted_data = format_ga4_report_data(ga4_report_data)
```

## Usage in Controllers

```python
@app.route('/report/<int:report_id>')
def view_report(report_id):
    # Get report data
    report_data = report_service.get_report_data(report_id)
    
    # Format dates
    created_at = format_date(report.created_at, format_str="%B %d, %Y")
    
    # Format metrics for display
    total_users = format_number(report_data.get('totalUsers', 0))
    bounce_rate = format_percentage(report_data.get('bounceRate', 0))
    session_duration = format_duration(report_data.get('avgSessionDuration', 0))
    
    return render_template('report.html',
                          created_at=created_at,
                          total_users=total_users,
                          bounce_rate=bounce_rate,
                          session_duration=session_duration)
```

## Template Filters

The formatters are registered as template filters for easy use in templates:

```html
<div class="dashboard-metrics">
    <div class="metric">
        <h3>{{ 'totalUsers'|format_metric_name }}</h3>
        <p class="value">{{ total_users|format_number(abbreviate=True) }}</p>
    </div>
    
    <div class="metric">
        <h3>{{ 'bounceRate'|format_metric_name }}</h3>
        <p class="value">{{ bounce_rate|format_percentage }}</p>
    </div>
    
    <div class="metric">
        <h3>{{ 'avgSessionDuration'|format_metric_name }}</h3>
        <p class="value">{{ avg_session_duration|format_duration }}</p>
    </div>
</div>

<p class="report-footer">
    Report generated on {{ report_date|format_date(format_str="%B %d, %Y at %H:%M") }}
</p>
```

## Best Practices

1. **Consistency**: Use formatters consistently throughout the application
2. **Type Safety**: Format functions handle string inputs safely but consider validating inputs
3. **Localization**: For multi-language support, consider locale in formatter functions
4. **Accessibility**: Ensure numeric values are presented in a way that screen readers can interpret
5. **Template Filters**: Use template filters in templates rather than formatting in controllers

## Configuration

The formatters are automatically registered as template filters during application initialization in `app.utils.init_utils()`. No additional configuration is required.