import json
from datetime import datetime, timedelta, date
from flask import current_app

def extract_metric_values(report_data, metric_name):
    """
    Extract metric values from report data.
    
    Args:
        report_data (dict): The report data.
        metric_name (str): The name of the metric to extract.
        
    Returns:
        list: A list of metric values.
    """
    if not report_data or 'rows' not in report_data:
        return []
    
    # Find the index of the metric in the headers
    metric_index = -1
    for i, header in enumerate(report_data['metricHeaders']):
        if header['name'] == metric_name:
            metric_index = i
            break
    
    if metric_index == -1:
        return []
    
    # Extract values
    values = []
    for row in report_data['rows']:
        if metric_index < len(row['metricValues']):
            try:
                value = float(row['metricValues'][metric_index]['value'])
                values.append(value)
            except (ValueError, TypeError):
                values.append(0)
    
    return values

def extract_dimension_values(report_data, dimension_name):
    """
    Extract dimension values from report data.
    
    Args:
        report_data (dict): The report data.
        dimension_name (str): The name of the dimension to extract.
        
    Returns:
        list: A list of dimension values.
    """
    if not report_data or 'rows' not in report_data:
        return []
    
    # Find the index of the dimension in the headers
    dimension_index = -1
    for i, header in enumerate(report_data['dimensionHeaders']):
        if header['name'] == dimension_name:
            dimension_index = i
            break
    
    if dimension_index == -1:
        return []
    
    # Extract values
    values = []
    for row in report_data['rows']:
        if dimension_index < len(row['dimensionValues']):
            values.append(row['dimensionValues'][dimension_index]['value'])
    
    return values

def get_date_range_for_form(days_ago=30):
    """
    Get date range for form.
    
    Args:
        days_ago (int): Number of days ago for the start date.
        
    Returns:
        tuple: A tuple of (start_date, end_date) as strings in YYYY-MM-DD format.
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=days_ago)
    
    return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')

def format_date_for_display(date_obj):
    """
    Format date for display.
    
    Args:
        date_obj (date): The date object to format.
        
    Returns:
        str: The formatted date string.
    """
    if isinstance(date_obj, str):
        try:
            date_obj = datetime.strptime(date_obj, '%Y-%m-%d').date()
        except ValueError:
            try:
                date_obj = datetime.strptime(date_obj, '%Y%m%d').date()
            except ValueError:
                return date_obj
    
    return date_obj.strftime('%b %d, %Y')

def calculate_percentage(part, whole):
    """
    Calculate percentage.
    
    Args:
        part (float): The part value.
        whole (float): The whole value.
        
    Returns:
        float: The percentage value.
    """
    if whole == 0:
        return 0
    return (part / whole) * 100

def format_number(number, decimal_places=0):
    """
    Format number with thousands separator and optional decimal places.
    
    Args:
        number (float): The number to format.
        decimal_places (int): The number of decimal places.
        
    Returns:
        str: The formatted number string.
    """
    if number is None:
        return "0"
    
    try:
        if decimal_places > 0:
            return f"{number:,.{decimal_places}f}"
        return f"{int(number):,}"
    except (ValueError, TypeError):
        return str(number)

def format_duration(seconds):
    """
    Format duration in seconds to a human-readable string.
    
    Args:
        seconds (float): The duration in seconds.
        
    Returns:
        str: The formatted duration string.
    """
    if seconds is None:
        return "0s"
    
    try:
        seconds = float(seconds)
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        
        if hours > 0:
            return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
        elif minutes > 0:
            return f"{int(minutes)}m {int(seconds)}s"
        else:
            return f"{int(seconds)}s"
    except (ValueError, TypeError):
        return str(seconds)

def get_comparison_data(current_value, previous_value):
    """
    Get comparison data between current and previous values.
    
    Args:
        current_value (float): The current value.
        previous_value (float): The previous value.
        
    Returns:
        dict: A dictionary with comparison data.
    """
    if previous_value == 0:
        percent_change = 100 if current_value > 0 else 0
    else:
        percent_change = ((current_value - previous_value) / previous_value) * 100
    
    return {
        'current': current_value,
        'previous': previous_value,
        'change': current_value - previous_value,
        'percent_change': percent_change,
        'is_increase': current_value > previous_value
    }

def get_top_items(report_data, dimension_name, metric_name, limit=10):
    """
    Get top items from report data.
    
    Args:
        report_data (dict): The report data.
        dimension_name (str): The name of the dimension to group by.
        metric_name (str): The name of the metric to sort by.
        limit (int): The maximum number of items to return.
        
    Returns:
        list: A list of dictionaries with dimension and metric values.
    """
    if not report_data or 'rows' not in report_data:
        return []
    
    # Find the indices of the dimension and metric in the headers
    dimension_index = -1
    for i, header in enumerate(report_data['dimensionHeaders']):
        if header['name'] == dimension_name:
            dimension_index = i
            break
    
    metric_index = -1
    for i, header in enumerate(report_data['metricHeaders']):
        if header['name'] == metric_name:
            metric_index = i
            break
    
    if dimension_index == -1 or metric_index == -1:
        return []
    
    # Extract dimension and metric values
    items = []
    for row in report_data['rows']:
        if dimension_index < len(row['dimensionValues']) and metric_index < len(row['metricValues']):
            dimension_value = row['dimensionValues'][dimension_index]['value']
            try:
                metric_value = float(row['metricValues'][metric_index]['value'])
            except (ValueError, TypeError):
                metric_value = 0
            
            items.append({
                'dimension': dimension_value,
                'metric': metric_value
            })
    
    # Sort by metric value in descending order and limit the results
    items.sort(key=lambda x: x['metric'], reverse=True)
    return items[:limit]

def aggregate_metrics(report_data, metrics):
    """
    Aggregate metrics from report data.
    
    Args:
        report_data (dict): The report data.
        metrics (list): A list of metric names to aggregate.
        
    Returns:
        dict: A dictionary of aggregated metric values.
    """
    result = {}
    
    for metric in metrics:
        values = extract_metric_values(report_data, metric)
        if values:
            result[metric] = sum(values)
        else:
            result[metric] = 0
    
    return result

def parse_json_data(json_string):
    """
    Parse JSON data from a string.
    
    Args:
        json_string (str): The JSON string to parse.
        
    Returns:
        dict: The parsed JSON data or None if parsing fails.
    """
    if not json_string:
        return None
    
    try:
        return json.loads(json_string)
    except json.JSONDecodeError as e:
        current_app.logger.error(f"Error parsing JSON data: {e}")
        return None

def get_date_dimension_index(report_data):
    """
    Get the index of the date dimension in report data.
    
    Args:
        report_data (dict): The report data.
        
    Returns:
        int: The index of the date dimension or -1 if not found.
    """
    if not report_data or 'dimensionHeaders' not in report_data:
        return -1
    
    for i, header in enumerate(report_data['dimensionHeaders']):
        if header['name'] == 'date':
            return i
    
    return -1

def get_time_series_data(report_data, metric_name):
    """
    Get time series data from report data.
    
    Args:
        report_data (dict): The report data.
        metric_name (str): The name of the metric to extract.
        
    Returns:
        dict: A dictionary with dates as keys and metric values as values.
    """
    if not report_data or 'rows' not in report_data:
        return {}
    
    # Find the indices of the date dimension and metric in the headers
    date_index = get_date_dimension_index(report_data)
    
    metric_index = -1
    for i, header in enumerate(report_data['metricHeaders']):
        if header['name'] == metric_name:
            metric_index = i
            break
    
    if date_index == -1 or metric_index == -1:
        return {}
    
    # Extract date and metric values
    time_series = {}
    for row in report_data['rows']:
        if date_index < len(row['dimensionValues']) and metric_index < len(row['metricValues']):
            date_str = row['dimensionValues'][date_index]['value']
            try:
                # Convert YYYYMMDD to YYYY-MM-DD
                date_obj = datetime.strptime(date_str, '%Y%m%d').date()
                date_key = date_obj.strftime('%Y-%m-%d')
                
                metric_value = float(row['metricValues'][metric_index]['value'])
                time_series[date_key] = metric_value
            except (ValueError, TypeError):
                continue
    
    return time_series