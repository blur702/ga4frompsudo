import json
import logging
import concurrent.futures
from datetime import datetime, date
from flask import current_app
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportRequest, DateRange, Dimension, Metric,
    BatchRunReportsRequest, BatchRunReportsResponse
)
from google.analytics.admin_v1alpha import AnalyticsAdminServiceClient
from google.analytics.admin_v1alpha.types import ListAccountSummariesRequest, ListDataStreamsRequest
from google.api_core.exceptions import GoogleAPIError, RetryError, ResourceExhausted
from google.oauth2.service_account import Credentials as ServiceAccountCredentials

from modules.auth import build_credentials
from modules.models import db, Property, AnalyticsData, StructuredMetric, MetricDefinition, Setting

# Maximum number of dimensions to include in a single API request
MAX_DIMENSIONS_PER_REQUEST = 9

# Maximum number of concurrent API requests
MAX_CONCURRENT_REQUESTS = 5

# Timeout for API requests in seconds
API_REQUEST_TIMEOUT = 60

def get_admin_service():
    """
    Get an authenticated Admin API client.
    
    Returns:
        AnalyticsAdminServiceClient or None: The Admin API client or None if authentication fails.
    """
    # Try to use OAuth credentials first
    credentials = build_credentials()
    if credentials:
        try:
            return AnalyticsAdminServiceClient(credentials=credentials)
        except Exception as e:
            current_app.logger.warning(f"Error creating Admin API client with OAuth: {e}")
    
    # Fall back to API key if available
    api_key = Setting.get_value('google_api_key')
    if api_key:
        try:
            # For API key authentication, we need to create service account credentials
            service_account_info = {
                "type": "service_account",
                "project_id": "ga4-dashboard",
                "private_key": api_key,
                "client_email": "ga4-dashboard@example.com",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
            service_credentials = ServiceAccountCredentials.from_service_account_info(
                service_account_info,
                scopes=['https://www.googleapis.com/auth/analytics.readonly']
            )
            return AnalyticsAdminServiceClient(credentials=service_credentials)
        except Exception as e:
            current_app.logger.error(f"Error creating Admin API client with API key: {e}")
    
    return None

def get_data_service():
    """
    Get an authenticated Data API client.
    
    Returns:
        BetaAnalyticsDataClient or None: The Data API client or None if authentication fails.
    """
    # Try to use OAuth credentials first
    credentials = build_credentials()
    if credentials:
        try:
            return BetaAnalyticsDataClient(credentials=credentials)
        except Exception as e:
            current_app.logger.warning(f"Error creating Data API client with OAuth: {e}")
    
    # Fall back to API key if available
    api_key = Setting.get_value('google_api_key')
    if api_key:
        try:
            # For API key authentication, we need to create service account credentials
            service_account_info = {
                "type": "service_account",
                "project_id": "ga4-dashboard",
                "private_key": api_key,
                "client_email": "ga4-dashboard@example.com",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
            service_credentials = ServiceAccountCredentials.from_service_account_info(
                service_account_info,
                scopes=['https://www.googleapis.com/auth/analytics.readonly']
            )
            return BetaAnalyticsDataClient(credentials=service_credentials)
        except Exception as e:
            current_app.logger.error(f"Error creating Data API client with API key: {e}")
    
    return None

def list_ga4_properties():
    """
    List all GA4 properties accessible to the authenticated user.
    
    Returns:
        list: A list of property dictionaries or an empty list if an error occurs.
    """
    admin_service = get_admin_service()
    if not admin_service:
        return []
    
    try:
        # List account summaries
        request = ListAccountSummariesRequest()
        response = admin_service.list_account_summaries(request)
        
        properties = []
        
        # Extract properties from account summaries
        for account in response:
            for property_summary in account.property_summaries:
                property_id = property_summary.property
                
                # Get website URL from data streams
                website_url = None
                try:
                    streams_request = ListDataStreamsRequest(parent=property_id)
                    streams_response = admin_service.list_data_streams(streams_request)
                    
                    for stream in streams_response:
                        if stream.web_stream_data:
                            website_url = stream.web_stream_data.default_uri
                            break
                except Exception as e:
                    current_app.logger.warning(f"Error getting data streams for property {property_id}: {e}")
                
                properties.append({
                    'ga_property_id': property_id,
                    'display_name': property_summary.display_name,
                    'website_url': website_url
                })
        
        return properties
    
    except Exception as e:
        current_app.logger.error(f"Error listing GA4 properties: {e}")
        return []

def sync_ga4_properties():
    """
    Synchronize GA4 properties with the database.
    
    Returns:
        list: A list of Property objects.
    """
    properties_data = list_ga4_properties()
    
    # Update existing properties and add new ones
    properties = []
    for prop_data in properties_data:
        property = Property.query.filter_by(ga_property_id=prop_data['ga_property_id']).first()
        
        if property:
            # Update existing property
            property.display_name = prop_data['display_name']
            property.website_url = prop_data['website_url']
            property.last_synced = datetime.utcnow()
        else:
            # Create new property
            property = Property(
                ga_property_id=prop_data['ga_property_id'],
                display_name=prop_data['display_name'],
                website_url=prop_data['website_url'],
                exclude_from_global_reports=False,
                last_synced=datetime.utcnow()
            )
            db.session.add(property)
        
        properties.append(property)
    
    db.session.commit()
    return properties

def get_analytics_report(property_id, start_date, end_date, dimensions, metrics):
    """
    Fetch analytics data from the GA4 API.
    
    Args:
        property_id (str): The GA4 property ID.
        start_date (str): The start date in YYYY-MM-DD format.
        end_date (str): The end date in YYYY-MM-DD format.
        dimensions (list): A list of dimension names.
        metrics (list): A list of metric names.
        
    Returns:
        str: JSON string of report data or None if an error occurs.
    """
    data_service = get_data_service()
    if not data_service:
        return None
    
    try:
        # Create dimension objects
        dimension_objects = [Dimension(name=dim) for dim in dimensions]
        
        # Create metric objects
        metric_objects = [Metric(name=met) for met in metrics]
        
        # Create date range
        date_range = DateRange(start_date=start_date, end_date=end_date)
        
        # Create request
        request = RunReportRequest(
            property=f"properties/{property_id}",
            dimensions=dimension_objects,
            metrics=metric_objects,
            date_ranges=[date_range]
        )
        
        # Run report
        response = data_service.run_report(request)
        
        # Convert response to JSON
        result = {
            "dimensionHeaders": [{"name": header.name} for header in response.dimension_headers],
            "metricHeaders": [{"name": header.name, "type": header.type_.name} for header in response.metric_headers],
            "rows": []
        }
        
        for row in response.rows:
            result_row = {
                "dimensionValues": [{"value": value.value} for value in row.dimension_values],
                "metricValues": [{"value": value.value} for value in row.metric_values]
            }
            result["rows"].append(result_row)
        
        return json.dumps(result)
    
    except GoogleAPIError as e:
        current_app.logger.error(f"Google API error fetching analytics data: {e}")
        return None
    except Exception as e:
        current_app.logger.error(f"Error fetching analytics data: {e}")
        return None

def fetch_and_store_analytics_report(property_id, start_date, end_date, dimensions, metrics):
    """
    Fetch analytics data from the GA4 API and store it in the database.
    
    Args:
        property_id (str): The GA4 property ID.
        start_date (str): The start date in YYYY-MM-DD format.
        end_date (str): The end date in YYYY-MM-DD format.
        dimensions (list): A list of dimension names.
        metrics (list): A list of metric names.
        
    Returns:
        AnalyticsData: The created AnalyticsData object or None if an error occurs.
    """
    # Get property from database
    property = Property.query.filter_by(ga_property_id=property_id).first()
    if not property:
        current_app.logger.error(f"Property not found: {property_id}")
        return None
    
    # Fetch analytics data
    raw_data_json = get_analytics_report_with_dimension_batching(
        property_id, start_date, end_date, dimensions, metrics
    )
    
    if not raw_data_json:
        return None
    
    # Create analytics data record
    analytics_data = AnalyticsData(
        property_id=property.id,
        report_start_date=datetime.strptime(start_date, "%Y-%m-%d").date(),
        report_end_date=datetime.strptime(end_date, "%Y-%m-%d").date(),
        raw_data_json=raw_data_json
    )
    
    db.session.add(analytics_data)
    db.session.commit()
    
    # Process and store structured metrics
    process_structured_metrics(analytics_data, property)
    
    return analytics_data

def batch_fetch_analytics_data(start_date, end_date, dimensions, metrics, property_ids):
    """
    Fetch analytics data for multiple properties.
    
    Args:
        start_date (str): The start date in YYYY-MM-DD format.
        end_date (str): The end date in YYYY-MM-DD format.
        dimensions (list): A list of dimension names.
        metrics (list): A list of metric names.
        property_ids (list): A list of GA4 property IDs.
        
    Returns:
        list: A list of AnalyticsData objects.
    """
    results = []
    
    # Validate metrics and dimensions
    valid_metrics, valid_dimensions = validate_metrics_and_dimensions(metrics, dimensions)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT_REQUESTS) as executor:
        # Create a future for each property
        future_to_property = {
            executor.submit(
                fetch_and_store_analytics_report, 
                property_id, 
                start_date, 
                end_date, 
                valid_dimensions, 
                valid_metrics
            ): property_id for property_id in property_ids
        }
        
        # Process results as they complete
        for future in concurrent.futures.as_completed(future_to_property):
            property_id = future_to_property[future]
            try:
                analytics_data = future.result(timeout=API_REQUEST_TIMEOUT)
                if analytics_data:
                    results.append(analytics_data)
            except concurrent.futures.TimeoutError:
                current_app.logger.error(f"Timeout fetching analytics data for property {property_id}")
            except Exception as e:
                current_app.logger.error(f"Error fetching analytics data for property {property_id}: {e}")
    
    return results

def validate_metrics_and_dimensions(metrics, dimensions):
    """
    Validate metrics and dimensions against the database.
    
    Args:
        metrics (list): A list of metric names.
        dimensions (list): A list of dimension names.
        
    Returns:
        tuple: A tuple of (valid_metrics, valid_dimensions).
    """
    # Get valid metrics from database
    valid_metric_names = [m.api_name for m in MetricDefinition.query.filter(
        MetricDefinition.api_name.in_(metrics),
        MetricDefinition.is_deprecated == False
    ).all()]
    
    # If no valid metrics found in database, use the provided metrics
    if not valid_metric_names and metrics:
        valid_metric_names = metrics
    
    # For dimensions, we don't have a comprehensive list in the database yet,
    # so we'll just use the provided dimensions for now
    valid_dimension_names = dimensions
    
    return valid_metric_names, valid_dimension_names

def get_analytics_report_with_dimension_batching(property_id, start_date, end_date, dimensions, metrics):
    """
    Fetch analytics data with dimension batching to handle the GA4 API limit of 9 dimensions per request.
    
    Args:
        property_id (str): The GA4 property ID.
        start_date (str): The start date in YYYY-MM-DD format.
        end_date (str): The end date in YYYY-MM-DD format.
        dimensions (list): A list of dimension names.
        metrics (list): A list of metric names.
        
    Returns:
        str: JSON string of combined report data or None if an error occurs.
    """
    # If we have 9 or fewer dimensions, we can make a single request
    if len(dimensions) <= MAX_DIMENSIONS_PER_REQUEST:
        return get_analytics_report(property_id, start_date, end_date, dimensions, metrics)
    
    # Otherwise, we need to batch the dimensions
    # We'll always include 'date' as a common dimension for joining results
    common_dimensions = ['date']
    remaining_dimensions = [d for d in dimensions if d not in common_dimensions]
    
    # Create batches of dimensions
    dimension_batches = []
    for i in range(0, len(remaining_dimensions), MAX_DIMENSIONS_PER_REQUEST - len(common_dimensions)):
        batch = common_dimensions + remaining_dimensions[i:i + MAX_DIMENSIONS_PER_REQUEST - len(common_dimensions)]
        dimension_batches.append(batch)
    
    # Fetch data for each batch
    results = []
    for batch in dimension_batches:
        result = get_analytics_report(property_id, start_date, end_date, batch, metrics)
        if result:
            results.append(result)
    
    # Join the results
    if results:
        return join_analytics_results(results, common_dimensions)
    
    return None

def join_analytics_results(results, common_dimensions):
    """
    Join results from multiple dimension batches.
    
    Args:
        results (list): A list of JSON strings of report data.
        common_dimensions (list): A list of common dimension names used for joining.
        
    Returns:
        str: JSON string of combined results.
    """
    # Parse JSON results
    parsed_results = [json.loads(result) for result in results]
    
    # If we only have one result, return it
    if len(parsed_results) == 1:
        return results[0]
    
    # Get the first result as the base
    base_result = parsed_results[0]
    
    # Create a dictionary to map common dimension values to rows
    dimension_map = {}
    
    # Find the indices of common dimensions in the base result
    common_indices = []
    for common_dim in common_dimensions:
        for i, header in enumerate(base_result['dimensionHeaders']):
            if header['name'] == common_dim:
                common_indices.append(i)
                break
    
    # Create a key for each row based on common dimension values
    for row in base_result['rows']:
        key = tuple(row['dimensionValues'][i]['value'] for i in common_indices)
        dimension_map[key] = row
    
    # Merge additional results
    for result in parsed_results[1:]:
        # Find the indices of common dimensions in this result
        result_common_indices = []
        for common_dim in common_dimensions:
            for i, header in enumerate(result['dimensionHeaders']):
                if header['name'] == common_dim:
                    result_common_indices.append(i)
                    break
        
        # Find the indices of non-common dimensions in this result
        non_common_indices = [i for i in range(len(result['dimensionHeaders'])) if i not in result_common_indices]
        
        # Add non-common dimension headers to the base result
        for i in non_common_indices:
            base_result['dimensionHeaders'].append(result['dimensionHeaders'][i])
        
        # Merge rows
        for row in result['rows']:
            key = tuple(row['dimensionValues'][i]['value'] for i in result_common_indices)
            
            if key in dimension_map:
                # Add non-common dimension values to the existing row
                for i in non_common_indices:
                    dimension_map[key]['dimensionValues'].append(row['dimensionValues'][i])
            else:
                # Create a new row with placeholder values for dimensions from the base result
                new_row = {
                    'dimensionValues': [{'value': ''} for _ in range(len(base_result['dimensionHeaders']))],
                    'metricValues': row['metricValues']
                }
                
                # Fill in common dimension values
                for base_idx, result_idx in zip(common_indices, result_common_indices):
                    new_row['dimensionValues'][base_idx] = row['dimensionValues'][result_idx]
                
                # Fill in non-common dimension values
                for i, result_idx in enumerate(non_common_indices):
                    new_row['dimensionValues'][len(base_result['dimensionHeaders']) - len(non_common_indices) + i] = row['dimensionValues'][result_idx]
                
                dimension_map[key] = new_row
    
    # Update the rows in the base result
    base_result['rows'] = list(dimension_map.values())
    
    return json.dumps(base_result)

def process_structured_metrics(analytics_data, property):
    """
    Process and store structured metrics from raw analytics data.
    
    Args:
        analytics_data (AnalyticsData): The AnalyticsData object.
        property (Property): The Property object.
    """
    raw_data = analytics_data.get_raw_data()
    if not raw_data or 'rows' not in raw_data:
        return
    
    # Get dimension and metric headers
    dimension_headers = [header['name'] for header in raw_data['dimensionHeaders']]
    metric_headers = [header['name'] for header in raw_data['metricHeaders']]
    
    # Find the date dimension index
    date_index = -1
    for i, header in enumerate(dimension_headers):
        if header == 'date':
            date_index = i
            break
    
    # Process each row
    for row in raw_data['rows']:
        # Get date value
        date_value = None
        if date_index >= 0 and date_index < len(row['dimensionValues']):
            date_str = row['dimensionValues'][date_index]['value']
            try:
                # Convert YYYYMMDD to date object
                date_value = datetime.strptime(date_str, "%Y%m%d").date()
            except ValueError:
                current_app.logger.warning(f"Invalid date format: {date_str}")
                continue
        else:
            # Use the report start date if no date dimension
            date_value = analytics_data.report_start_date
        
        # Create dimensions dictionary
        dimensions_dict = {}
        for i, header in enumerate(dimension_headers):
            if i < len(row['dimensionValues']):
                dimensions_dict[header] = row['dimensionValues'][i]['value']
        
        # Process each metric
        for i, metric_name in enumerate(metric_headers):
            if i < len(row['metricValues']):
                metric_value_str = row['metricValues'][i]['value']
                try:
                    metric_value = float(metric_value_str)
                except ValueError:
                    current_app.logger.warning(f"Invalid metric value: {metric_value_str}")
                    continue
                
                # Get or create metric definition
                metric_definition = MetricDefinition.query.filter_by(api_name=metric_name).first()
                if not metric_definition:
                    metric_definition = MetricDefinition(
                        api_name=metric_name,
                        display_name=metric_name,
                        aggregation_type="sum"
                    )
                    db.session.add(metric_definition)
                    db.session.flush()
                
                # Create structured metric
                structured_metric = StructuredMetric(
                    analytics_data_id=analytics_data.id,
                    property_id=property.id,
                    metric_id=metric_definition.id,
                    date=date_value,
                    value=metric_value
                )
                structured_metric.set_dimensions(dimensions_dict)
                
                db.session.add(structured_metric)
    
    db.session.commit()