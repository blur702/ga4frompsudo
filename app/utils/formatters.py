"""
Formatter utilities for the GA4 Analytics Dashboard.

This module provides various formatters for:
- Numbers (views, users, etc.)
- Percentages (bounce rates, etc.)
- Dates and durations
- File sizes
- CSV and JSON data
"""

import json
import csv
import io
import re
import math
import datetime
from typing import Any, Dict, List, Union, Optional

def format_number(value: Union[int, float, str], 
                  precision: int = 0, 
                  abbreviate: bool = False,
                  locale: str = 'en_US') -> str:
    """
    Format a number with proper thousands separators and optional abbreviation.
    
    Args:
        value: Number to format
        precision: Number of decimal places
        abbreviate: Whether to abbreviate large numbers (K, M, B)
        locale: Locale code for formatting (currently only supports en_US)
        
    Returns:
        Formatted number string
    """
    try:
        # Convert to float if it's a string or other numeric type
        num = float(value)
    except (ValueError, TypeError):
        return str(value)
    
    # Abbreviate large numbers if requested
    if abbreviate:
        if abs(num) >= 1_000_000_000:
            return f"{num / 1_000_000_000:.{precision}f}B"
        elif abs(num) >= 1_000_000:
            return f"{num / 1_000_000:.{precision}f}M"
        elif abs(num) >= 1_000:
            return f"{num / 1_000:.{precision}f}K"
    
    # Format with thousands separator and decimal places
    if precision == 0:
        return f"{int(num):,}"
    
    return f"{num:,.{precision}f}"

def format_percentage(value: Union[float, str], 
                      precision: int = 2, 
                      include_sign: bool = True) -> str:
    """
    Format a value as a percentage.
    
    Args:
        value: Number to format (0.75 = 75%)
        precision: Number of decimal places
        include_sign: Whether to include the % sign
        
    Returns:
        Formatted percentage string
    """
    try:
        # Convert to float if it's a string or other numeric type
        num = float(value)
    except (ValueError, TypeError):
        return str(value)
    
    # Check if the value is already a percentage (> 1)
    if abs(num) <= 1:
        num *= 100
    
    # Format with specified precision
    if precision == 0:
        formatted = f"{int(num)}"
    else:
        formatted = f"{num:.{precision}f}"
    
    # Add percentage sign if requested
    if include_sign:
        return f"{formatted}%"
    
    return formatted

def format_date(date_value: Union[str, datetime.date, datetime.datetime],
                format_str: str = '%Y-%m-%d',
                localize: bool = False) -> str:
    """
    Format a date in the specified format.
    
    Args:
        date_value: Date to format
        format_str: strftime format string
        localize: Whether to localize month/day names (currently not implemented)
        
    Returns:
        Formatted date string
    """
    # If it's already a string, try to parse it
    if isinstance(date_value, str):
        # Try different formats
        for fmt in ('%Y-%m-%d', '%Y%m%d', '%d/%m/%Y', '%m/%d/%Y'):
            try:
                date_value = datetime.datetime.strptime(date_value, fmt).date()
                break
            except ValueError:
                continue
        
        # If still a string, just return it
        if isinstance(date_value, str):
            return date_value
    
    # If it's a datetime, convert to date if we only want date components
    if isinstance(date_value, datetime.datetime) and '%H' not in format_str and '%M' not in format_str:
        date_value = date_value.date()
    
    # Format the date
    try:
        return date_value.strftime(format_str)
    except (AttributeError, ValueError):
        return str(date_value)

def format_duration(seconds: Union[int, float, str], 
                    format_type: str = 'human') -> str:
    """
    Format a duration in seconds into a readable format.
    
    Args:
        seconds: Duration in seconds
        format_type: 'human' for human-readable (1h 2m 3s), 
                     'clock' for clock format (01:02:03),
                     'compact' for shortest representation (1h2m)
                     
    Returns:
        Formatted duration string
    """
    try:
        seconds = float(seconds)
    except (ValueError, TypeError):
        return str(seconds)
    
    # Calculate components
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    # Format based on type
    if format_type == 'clock':
        return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
    
    if format_type == 'compact':
        parts = []
        if hours:
            parts.append(f"{int(hours)}h")
        if minutes or (hours and seconds):
            parts.append(f"{int(minutes)}m")
        if seconds or not parts:
            parts.append(f"{int(seconds)}s")
        return "".join(parts)
    
    # Default: human-readable
    parts = []
    if hours:
        parts.append(f"{int(hours)}h")
    if minutes:
        parts.append(f"{int(minutes)}m")
    if seconds or not parts:
        parts.append(f"{int(seconds)}s")
    return " ".join(parts)

def format_file_size(size_bytes: Union[int, float, str], 
                     precision: int = 2) -> str:
    """
    Format a file size in bytes to a human-readable format.
    
    Args:
        size_bytes: Size in bytes
        precision: Number of decimal places
        
    Returns:
        Formatted size string (e.g., "2.5 MB")
    """
    try:
        size_bytes = float(size_bytes)
    except (ValueError, TypeError):
        return str(size_bytes)
    
    # Define size units
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    
    # Calculate appropriate unit
    if size_bytes == 0:
        return "0 B"
    
    i = int(math.floor(math.log(size_bytes, 1024)))
    if i >= len(units):
        i = len(units) - 1
    
    size = size_bytes / (1024 ** i)
    
    # Format with specified precision
    return f"{size:.{precision}f} {units[i]}"

def format_metric_name(metric_name: str) -> str:
    """
    Format a metric name from camelCase or snake_case to a human-readable format.
    
    Args:
        metric_name: Metric name (e.g., "screenPageViews", "avg_session_duration")
        
    Returns:
        Formatted metric name (e.g., "Screen Page Views", "Avg Session Duration")
    """
    # Handle snake_case
    if '_' in metric_name:
        words = metric_name.split('_')
        return ' '.join(word.capitalize() for word in words)
    
    # Handle camelCase
    # Insert a space before capital letters and then capitalize first letter
    metric_name = re.sub(r'([a-z])([A-Z])', r'\1 \2', metric_name)
    return metric_name[0].upper() + metric_name[1:]

def data_to_csv(data: List[Dict[str, Any]], 
                include_headers: bool = True) -> str:
    """
    Convert a list of dictionaries to CSV format.
    
    Args:
        data: List of dictionaries with the same structure
        include_headers: Whether to include header row
        
    Returns:
        CSV string
    """
    if not data:
        return ""
    
    # Create a StringIO object to write CSV data
    output = io.StringIO()
    
    # Get headers from first row
    headers = list(data[0].keys())
    
    # Create CSV writer
    writer = csv.DictWriter(output, fieldnames=headers)
    
    # Write headers if requested
    if include_headers:
        writer.writeheader()
    
    # Write data rows
    writer.writerows(data)
    
    # Get the CSV string
    csv_string = output.getvalue()
    output.close()
    
    return csv_string

def data_to_json(data: Any, pretty: bool = False) -> str:
    """
    Convert data to JSON format.
    
    Args:
        data: Data to convert (should be JSON-serializable)
        pretty: Whether to format with indentation
        
    Returns:
        JSON string
    """
    if pretty:
        return json.dumps(data, indent=2)
    return json.dumps(data)

def format_dimension_value(dimension: str, value: str) -> str:
    """
    Format a dimension value appropriately based on the dimension type.
    
    Args:
        dimension: The dimension name
        value: The dimension value
        
    Returns:
        Formatted dimension value
    """
    # Handle date dimensions
    if dimension in ('date', 'dateHour', 'dateHourMinute'):
        if dimension == 'date' and len(value) == 8:  # YYYYMMDD format
            return format_date(value, '%b %d, %Y')
        if dimension == 'dateHour' and len(value) == 10:  # YYYYMMDDHH format
            date_str = value[:8]
            hour = value[8:10]
            return f"{format_date(date_str, '%b %d, %Y')} {hour}:00"
    
    # Handle device category
    if dimension == 'deviceCategory':
        return value.capitalize()
    
    # Handle country
    if dimension == 'country':
        return value
    
    # Handle page path
    if dimension == 'pagePath':
        # Truncate very long paths
        if len(value) > 50:
            return value[:47] + '...'
        return value
    
    # Default: just return the value
    return value

def format_ga4_report_data(report_data: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Format GA4 API report data into a more user-friendly format.
    
    Args:
        report_data: Report data from GA4 API
        
    Returns:
        List of formatted data dictionaries
    """
    formatted_data = []
    
    # Extract headers
    dimension_headers = [h.get('name') for h in report_data.get('dimensionHeaders', [])]
    metric_headers = [h.get('name') for h in report_data.get('metricHeaders', [])]
    
    # Process rows
    for row in report_data.get('rows', []):
        data_row = {}
        
        # Add dimensions with formatting
        for i, dim in enumerate(row.get('dimensionValues', [])):
            if i < len(dimension_headers):
                dim_name = dimension_headers[i]
                dim_value = dim.get('value')
                data_row[dim_name] = format_dimension_value(dim_name, dim_value)
        
        # Add metrics with formatting
        for i, metric in enumerate(row.get('metricValues', [])):
            if i < len(metric_headers):
                metric_name = metric_headers[i]
                metric_value = metric.get('value')
                
                # Format based on metric type
                if metric_name.startswith('percent') or metric_name.endswith('Rate'):
                    data_row[metric_name] = format_percentage(metric_value)
                elif 'Duration' in metric_name:
                    data_row[metric_name] = format_duration(float(metric_value))
                elif any(name in metric_name.lower() for name in ['revenue', 'value', 'arpu']):
                    data_row[metric_name] = f"${float(metric_value):.2f}"
                else:
                    # Format as number
                    data_row[metric_name] = format_number(metric_value)
        
        formatted_data.append(data_row)
    
    return formatted_data