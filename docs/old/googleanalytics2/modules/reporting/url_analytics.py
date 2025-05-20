import re
from urllib.parse import urlparse
from flask import current_app

from modules.ga_api import get_analytics_report
from modules.reporting.common import (
    parse_json_data, aggregate_metrics, get_top_items,
    get_time_series_data, format_number, calculate_percentage
)

def generate_url_analytics_report(url, start_date, end_date, property_id, metrics, dimensions):
    """
    Generate URL analytics report for a specific URL.
    
    Args:
        url (str): The URL to analyze.
        start_date (str): The start date in YYYY-MM-DD format.
        end_date (str): The end date in YYYY-MM-DD format.
        property_id (str): The GA4 property ID.
        metrics (list): A list of metric names.
        dimensions (list): A list of dimension names.
        
    Returns:
        dict: The report data or None if an error occurs.
    """
    # Validate URL
    if not validate_url(url):
        current_app.logger.error(f"Invalid URL: {url}")
        return None
    
    # Get URL path
    url_path = get_url_path_from_full_url(url)
    
    # Ensure 'date' is in dimensions for time series data
    if 'date' not in dimensions:
        dimensions.append('date')
    
    # Ensure 'pagePathPlusQueryString' is in dimensions for filtering
    if 'pagePathPlusQueryString' not in dimensions:
        dimensions.append('pagePathPlusQueryString')
    
    # Get analytics data
    raw_data_json = get_analytics_report(property_id, start_date, end_date, dimensions, metrics)
    if not raw_data_json:
        return None
    
    # Parse JSON data
    report_data = parse_json_data(raw_data_json)
    if not report_data:
        return None
    
    # Filter data for the specific URL path
    filtered_data = filter_data_for_url(report_data, url_path)
    
    # Generate report
    return {
        'url': url,
        'url_path': url_path,
        'start_date': start_date,
        'end_date': end_date,
        'property_id': property_id,
        'metrics': metrics,
        'dimensions': dimensions,
        'aggregated_metrics': aggregate_metrics(filtered_data, metrics),
        'time_series': {metric: get_time_series_data(filtered_data, metric) for metric in metrics},
        'top_referrers': get_top_referrers(filtered_data),
        'top_devices': get_top_devices(filtered_data),
        'top_browsers': get_top_browsers(filtered_data),
        'top_countries': get_top_countries(filtered_data),
        'raw_data': filtered_data
    }

def get_url_path_from_full_url(url):
    """
    Extract path from URL.
    
    Args:
        url (str): The full URL.
        
    Returns:
        str: The URL path.
    """
    parsed_url = urlparse(url)
    path = parsed_url.path
    
    # Include query string if present
    if parsed_url.query:
        path += f"?{parsed_url.query}"
    
    # Include fragment if present
    if parsed_url.fragment:
        path += f"#{parsed_url.fragment}"
    
    return path

def validate_url(url):
    """
    Validate URL format.
    
    Args:
        url (str): The URL to validate.
        
    Returns:
        bool: True if valid, False otherwise.
    """
    if not url:
        return False
    
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False

def filter_data_for_url(report_data, url_path):
    """
    Filter report data for a specific URL path.
    
    Args:
        report_data (dict): The report data.
        url_path (str): The URL path to filter for.
        
    Returns:
        dict: The filtered report data.
    """
    if not report_data or 'rows' not in report_data:
        return report_data
    
    # Find the index of the pagePathPlusQueryString dimension
    path_index = -1
    for i, header in enumerate(report_data['dimensionHeaders']):
        if header['name'] == 'pagePathPlusQueryString':
            path_index = i
            break
    
    if path_index == -1:
        return report_data
    
    # Filter rows
    filtered_rows = []
    for row in report_data['rows']:
        if path_index < len(row['dimensionValues']):
            row_path = row['dimensionValues'][path_index]['value']
            if row_path == url_path:
                filtered_rows.append(row)
    
    # Create filtered data
    filtered_data = {
        'dimensionHeaders': report_data['dimensionHeaders'],
        'metricHeaders': report_data['metricHeaders'],
        'rows': filtered_rows
    }
    
    return filtered_data

def get_top_referrers(report_data, limit=10):
    """
    Get top referrers from report data.
    
    Args:
        report_data (dict): The report data.
        limit (int): The maximum number of referrers to return.
        
    Returns:
        list: A list of dictionaries with referrer and session count.
    """
    # Check if sessionSource dimension is available
    has_source = False
    for header in report_data.get('dimensionHeaders', []):
        if header['name'] == 'sessionSource':
            has_source = True
            break
    
    if not has_source:
        return []
    
    # Get top referrers by sessions
    top_referrers = get_top_items(report_data, 'sessionSource', 'sessions', limit)
    
    # Calculate total sessions
    total_sessions = sum(item['metric'] for item in top_referrers)
    
    # Add percentage
    for item in top_referrers:
        item['percentage'] = calculate_percentage(item['metric'], total_sessions)
        item['formatted_metric'] = format_number(item['metric'])
    
    return top_referrers

def get_top_devices(report_data, limit=5):
    """
    Get top devices from report data.
    
    Args:
        report_data (dict): The report data.
        limit (int): The maximum number of devices to return.
        
    Returns:
        list: A list of dictionaries with device and session count.
    """
    # Check if deviceCategory dimension is available
    has_device = False
    for header in report_data.get('dimensionHeaders', []):
        if header['name'] == 'deviceCategory':
            has_device = True
            break
    
    if not has_device:
        return []
    
    # Get top devices by sessions
    top_devices = get_top_items(report_data, 'deviceCategory', 'sessions', limit)
    
    # Calculate total sessions
    total_sessions = sum(item['metric'] for item in top_devices)
    
    # Add percentage
    for item in top_devices:
        item['percentage'] = calculate_percentage(item['metric'], total_sessions)
        item['formatted_metric'] = format_number(item['metric'])
    
    return top_devices

def get_top_browsers(report_data, limit=5):
    """
    Get top browsers from report data.
    
    Args:
        report_data (dict): The report data.
        limit (int): The maximum number of browsers to return.
        
    Returns:
        list: A list of dictionaries with browser and session count.
    """
    # Check if browser dimension is available
    has_browser = False
    for header in report_data.get('dimensionHeaders', []):
        if header['name'] == 'browser':
            has_browser = True
            break
    
    if not has_browser:
        return []
    
    # Get top browsers by sessions
    top_browsers = get_top_items(report_data, 'browser', 'sessions', limit)
    
    # Calculate total sessions
    total_sessions = sum(item['metric'] for item in top_browsers)
    
    # Add percentage
    for item in top_browsers:
        item['percentage'] = calculate_percentage(item['metric'], total_sessions)
        item['formatted_metric'] = format_number(item['metric'])
    
    return top_browsers

def get_top_countries(report_data, limit=10):
    """
    Get top countries from report data.
    
    Args:
        report_data (dict): The report data.
        limit (int): The maximum number of countries to return.
        
    Returns:
        list: A list of dictionaries with country and session count.
    """
    # Check if country dimension is available
    has_country = False
    for header in report_data.get('dimensionHeaders', []):
        if header['name'] == 'country':
            has_country = True
            break
    
    if not has_country:
        return []
    
    # Get top countries by sessions
    top_countries = get_top_items(report_data, 'country', 'sessions', limit)
    
    # Calculate total sessions
    total_sessions = sum(item['metric'] for item in top_countries)
    
    # Add percentage
    for item in top_countries:
        item['percentage'] = calculate_percentage(item['metric'], total_sessions)
        item['formatted_metric'] = format_number(item['metric'])
    
    return top_countries