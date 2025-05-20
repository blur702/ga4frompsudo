from flask import current_app
from datetime import datetime

from modules.models import Property
from modules.ga_api import get_analytics_report, batch_fetch_analytics_data
from modules.reporting.common import (
    parse_json_data, aggregate_metrics, get_top_items,
    get_time_series_data, format_number, calculate_percentage
)

def generate_property_aggregation_report(property_ids, start_date, end_date, metrics, dimensions):
    """
    Generate a report that aggregates data across multiple GA4 properties.
    
    Args:
        property_ids (list): A list of GA4 property IDs.
        start_date (str): The start date in YYYY-MM-DD format.
        end_date (str): The end date in YYYY-MM-DD format.
        metrics (list): A list of metric names.
        dimensions (list): A list of dimension names.
        
    Returns:
        dict: The report data or None if an error occurs.
    """
    # Validate inputs
    if not property_ids:
        current_app.logger.error("No property IDs provided")
        return None
    
    # Ensure 'date' is in dimensions for time series data
    if 'date' not in dimensions:
        dimensions.append('date')
    
    # Get property objects
    properties = Property.query.filter(Property.ga_property_id.in_(property_ids)).all()
    if not properties:
        current_app.logger.error("No valid properties found")
        return None
    
    # Fetch analytics data for all properties
    analytics_data_list = batch_fetch_analytics_data(
        start_date, end_date, dimensions, metrics, property_ids
    )
    
    # Process each property's data
    property_reports = []
    for property_obj in properties:
        # Find analytics data for this property
        analytics_data = next(
            (data for data in analytics_data_list if data.property_id == property_obj.id),
            None
        )
        
        if not analytics_data:
            # If no data was fetched, try to fetch it directly
            raw_data_json = get_analytics_report(
                property_obj.ga_property_id, start_date, end_date, dimensions, metrics
            )
            if not raw_data_json:
                current_app.logger.warning(f"No data available for property {property_obj.display_name}")
                continue
            
            report_data = parse_json_data(raw_data_json)
        else:
            report_data = analytics_data.get_raw_data()
        
        if not report_data:
            continue
        
        # Create property report
        property_report = {
            'property_id': property_obj.ga_property_id,
            'property_name': property_obj.display_name,
            'website_url': property_obj.website_url,
            'aggregated_metrics': aggregate_metrics(report_data, metrics),
            'time_series': {metric: get_time_series_data(report_data, metric) for metric in metrics},
            'raw_data': report_data
        }
        
        property_reports.append(property_report)
    
    # Aggregate metrics across all properties
    aggregated_metrics = aggregate_metrics_across_properties(property_reports, metrics)
    
    # Combine time series data
    combined_time_series = combine_time_series_data(property_reports, metrics)
    
    # Generate report
    return {
        'start_date': start_date,
        'end_date': end_date,
        'metrics': metrics,
        'dimensions': dimensions,
        'properties': property_reports,
        'aggregated_metrics': aggregated_metrics,
        'time_series': combined_time_series,
        'property_comparison': generate_property_comparison(property_reports, metrics),
        'report_generated_at': datetime.utcnow().isoformat()
    }

def aggregate_metrics_across_properties(property_reports, metrics):
    """
    Aggregate metrics across multiple properties.
    
    Args:
        property_reports (list): A list of property report dictionaries.
        metrics (list): A list of metric names.
        
    Returns:
        dict: A dictionary of aggregated metric values.
    """
    result = {metric: 0 for metric in metrics}
    
    for property_report in property_reports:
        property_metrics = property_report.get('aggregated_metrics', {})
        for metric in metrics:
            if metric in property_metrics:
                # Some metrics should be averaged rather than summed
                if metric.lower() in ['bounceRate', 'conversionRate', 'engagementRate']:
                    # These will be averaged later
                    result[metric] += property_metrics[metric]
                else:
                    result[metric] += property_metrics[metric]
    
    # Average rate metrics
    for metric in metrics:
        if metric.lower() in ['bounceRate', 'conversionRate', 'engagementRate']:
            if property_reports:
                result[metric] /= len(property_reports)
    
    return result

def combine_time_series_data(property_reports, metrics):
    """
    Combine time series data from multiple properties.
    
    Args:
        property_reports (list): A list of property report dictionaries.
        metrics (list): A list of metric names.
        
    Returns:
        dict: A dictionary of combined time series data.
    """
    result = {metric: {} for metric in metrics}
    
    for property_report in property_reports:
        property_time_series = property_report.get('time_series', {})
        
        for metric in metrics:
            if metric in property_time_series:
                metric_time_series = property_time_series[metric]
                
                for date_str, value in metric_time_series.items():
                    if date_str not in result[metric]:
                        result[metric][date_str] = 0
                    
                    # Some metrics should be averaged rather than summed
                    if metric.lower() in ['bounceRate', 'conversionRate', 'engagementRate']:
                        # These will be averaged later
                        result[metric][date_str] += value
                    else:
                        result[metric][date_str] += value
    
    # Average rate metrics
    for metric in metrics:
        if metric.lower() in ['bounceRate', 'conversionRate', 'engagementRate']:
            for date_str in result[metric]:
                # Count how many properties have data for this date
                count = sum(1 for report in property_reports if 
                           date_str in report.get('time_series', {}).get(metric, {}))
                if count > 0:
                    result[metric][date_str] /= count
    
    return result

def generate_property_comparison(property_reports, metrics):
    """
    Generate a comparison of metrics across properties.
    
    Args:
        property_reports (list): A list of property report dictionaries.
        metrics (list): A list of metric names.
        
    Returns:
        dict: A dictionary with metric comparisons.
    """
    result = {}
    
    for metric in metrics:
        property_values = []
        
        for property_report in property_reports:
            property_metrics = property_report.get('aggregated_metrics', {})
            if metric in property_metrics:
                property_values.append({
                    'property_id': property_report['property_id'],
                    'property_name': property_report['property_name'],
                    'value': property_metrics[metric]
                })
        
        # Sort by value in descending order
        property_values.sort(key=lambda x: x['value'], reverse=True)
        
        # Calculate total for percentage
        total = sum(item['value'] for item in property_values)
        
        # Add percentage and formatted value
        for item in property_values:
            item['percentage'] = calculate_percentage(item['value'], total)
            item['formatted_value'] = format_number(item['value'])
        
        result[metric] = property_values
    
    return result

def get_property_selection_sets():
    """
    Get all property selection sets from the database.
    
    Returns:
        list: A list of PropertySelectionSet objects.
    """
    from modules.models import PropertySelectionSet
    return PropertySelectionSet.query.order_by(PropertySelectionSet.name).all()

def get_property_selection_set(set_id):
    """
    Get a property selection set by ID.
    
    Args:
        set_id (int): The ID of the property selection set.
        
    Returns:
        PropertySelectionSet: The PropertySelectionSet object or None if not found.
    """
    from modules.models import PropertySelectionSet
    return PropertySelectionSet.query.get(set_id)

def create_property_selection_set(name, description, property_ids):
    """
    Create a new property selection set.
    
    Args:
        name (str): The name of the selection set.
        description (str): The description of the selection set.
        property_ids (list): A list of property IDs.
        
    Returns:
        PropertySelectionSet: The created PropertySelectionSet object.
    """
    from modules.models import db, PropertySelectionSet
    
    selection_set = PropertySelectionSet(
        name=name,
        description=description
    )
    selection_set.set_property_ids(property_ids)
    
    db.session.add(selection_set)
    db.session.commit()
    
    return selection_set

def update_property_selection_set(set_id, name, description, property_ids):
    """
    Update an existing property selection set.
    
    Args:
        set_id (int): The ID of the property selection set.
        name (str): The name of the selection set.
        description (str): The description of the selection set.
        property_ids (list): A list of property IDs.
        
    Returns:
        PropertySelectionSet: The updated PropertySelectionSet object or None if not found.
    """
    from modules.models import db, PropertySelectionSet
    
    selection_set = PropertySelectionSet.query.get(set_id)
    if not selection_set:
        return None
    
    selection_set.name = name
    selection_set.description = description
    selection_set.set_property_ids(property_ids)
    
    db.session.commit()
    
    return selection_set

def delete_property_selection_set(set_id):
    """
    Delete a property selection set.
    
    Args:
        set_id (int): The ID of the property selection set.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    from modules.models import db, PropertySelectionSet
    
    selection_set = PropertySelectionSet.query.get(set_id)
    if not selection_set:
        return False
    
    db.session.delete(selection_set)
    db.session.commit()
    
    return True