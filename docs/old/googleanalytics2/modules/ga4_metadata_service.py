import logging
from datetime import datetime
from flask import current_app
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import GetMetadataRequest
from google.api_core.exceptions import GoogleAPIError

from modules.auth import build_credentials
from modules.models import db, MetricDefinition, DimensionDefinition

def get_metadata_service():
    """
    Get an authenticated GA4 metadata service client.
    
    Returns:
        BetaAnalyticsDataClient or None: The metadata service client or None if authentication fails.
    """
    credentials = build_credentials()
    if not credentials:
        return None
    
    try:
        return BetaAnalyticsDataClient(credentials=credentials)
    except Exception as e:
        current_app.logger.error(f"Error creating metadata service client: {e}")
        return None

def update_ga4_metadata(property_id):
    """
    Update GA4 metadata (metrics and dimensions) for a specific property.
    
    Args:
        property_id (str): The GA4 property ID.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    metadata_service = get_metadata_service()
    if not metadata_service:
        return False
    
    try:
        # Get metadata for the property
        request = GetMetadataRequest(name=f"properties/{property_id}/metadata")
        metadata = metadata_service.get_metadata(request)
        
        # Process metrics
        for metric in metadata.metrics:
            update_metric_definition(metric)
        
        # Process dimensions
        for dimension in metadata.dimensions:
            update_dimension_definition(dimension)
        
        db.session.commit()
        return True
    
    except GoogleAPIError as e:
        current_app.logger.error(f"Google API error fetching metadata: {e}")
        return False
    except Exception as e:
        current_app.logger.error(f"Error updating GA4 metadata: {e}")
        db.session.rollback()
        return False

def update_metric_definition(metric):
    """
    Update or create a metric definition from GA4 metadata.
    
    Args:
        metric: The GA4 metric metadata.
    """
    # Find existing metric definition
    metric_definition = MetricDefinition.query.filter_by(api_name=metric.api_name).first()
    
    # Determine aggregation type
    aggregation_type = "sum"
    if "AVERAGE" in metric.api_name.upper() or "AVG" in metric.api_name.upper():
        aggregation_type = "average"
    elif "UNIQUE" in metric.api_name.upper() or "RATIO" in metric.api_name.upper():
        aggregation_type = "unique"
    
    # Determine category
    category = None
    if "USER" in metric.api_name.upper():
        category = "User"
    elif "SESSION" in metric.api_name.upper():
        category = "Session"
    elif "EVENT" in metric.api_name.upper():
        category = "Event"
    elif "CONVERSION" in metric.api_name.upper():
        category = "Conversion"
    elif "REVENUE" in metric.api_name.upper() or "ECOMMERCE" in metric.api_name.upper():
        category = "Revenue"
    
    if metric_definition:
        # Update existing metric definition
        metric_definition.display_name = metric.ui_name
        metric_definition.description = metric.description
        metric_definition.category = category
        metric_definition.aggregation_type = aggregation_type
        metric_definition.is_custom = metric.custom_definition
        metric_definition.is_deprecated = metric.deprecated
        metric_definition.last_updated = datetime.utcnow()
    else:
        # Create new metric definition
        metric_definition = MetricDefinition(
            api_name=metric.api_name,
            display_name=metric.ui_name,
            description=metric.description,
            category=category,
            aggregation_type=aggregation_type,
            is_custom=metric.custom_definition,
            is_deprecated=metric.deprecated,
            last_updated=datetime.utcnow()
        )
        db.session.add(metric_definition)

def update_dimension_definition(dimension):
    """
    Update or create a dimension definition from GA4 metadata.
    
    Args:
        dimension: The GA4 dimension metadata.
    """
    # Find existing dimension definition
    dimension_definition = DimensionDefinition.query.filter_by(api_name=dimension.api_name).first()
    
    # Determine category
    category = None
    if "DATE" in dimension.api_name.upper() or "TIME" in dimension.api_name.upper():
        category = "Time"
    elif "GEO" in dimension.api_name.upper() or "COUNTRY" in dimension.api_name.upper() or "CITY" in dimension.api_name.upper():
        category = "Geography"
    elif "DEVICE" in dimension.api_name.upper() or "BROWSER" in dimension.api_name.upper() or "OS" in dimension.api_name.upper():
        category = "Technology"
    elif "PAGE" in dimension.api_name.upper() or "SCREEN" in dimension.api_name.upper() or "URL" in dimension.api_name.upper():
        category = "Content"
    elif "SOURCE" in dimension.api_name.upper() or "MEDIUM" in dimension.api_name.upper() or "CAMPAIGN" in dimension.api_name.upper():
        category = "Traffic Source"
    elif "USER" in dimension.api_name.upper():
        category = "User"
    elif "EVENT" in dimension.api_name.upper():
        category = "Event"
    
    if dimension_definition:
        # Update existing dimension definition
        dimension_definition.display_name = dimension.ui_name
        dimension_definition.description = dimension.description
        dimension_definition.category = category
        dimension_definition.is_custom = dimension.custom_definition
        dimension_definition.is_deprecated = dimension.deprecated
        dimension_definition.last_updated = datetime.utcnow()
    else:
        # Create new dimension definition
        dimension_definition = DimensionDefinition(
            api_name=dimension.api_name,
            display_name=dimension.ui_name,
            description=dimension.description,
            category=category,
            is_custom=dimension.custom_definition,
            is_deprecated=dimension.deprecated,
            last_updated=datetime.utcnow()
        )
        db.session.add(dimension_definition)

def get_available_metrics():
    """
    Get all available metrics from the database.
    
    Returns:
        list: A list of metric dictionaries.
    """
    metrics = MetricDefinition.query.filter_by(is_deprecated=False).order_by(MetricDefinition.display_name).all()
    return [metric.to_dict() for metric in metrics]

def get_available_dimensions():
    """
    Get all available dimensions from the database.
    
    Returns:
        list: A list of dimension dictionaries.
    """
    dimensions = DimensionDefinition.query.filter_by(is_deprecated=False).order_by(DimensionDefinition.display_name).all()
    return [dimension.to_dict() for dimension in dimensions]

def get_metrics_by_category():
    """
    Get metrics grouped by category.
    
    Returns:
        dict: A dictionary of metrics grouped by category.
    """
    metrics = MetricDefinition.query.filter_by(is_deprecated=False).order_by(MetricDefinition.category, MetricDefinition.display_name).all()
    
    result = {}
    for metric in metrics:
        category = metric.category or "Other"
        if category not in result:
            result[category] = []
        result[category].append(metric.to_dict())
    
    return result

def get_dimensions_by_category():
    """
    Get dimensions grouped by category.
    
    Returns:
        dict: A dictionary of dimensions grouped by category.
    """
    dimensions = DimensionDefinition.query.filter_by(is_deprecated=False).order_by(DimensionDefinition.category, DimensionDefinition.display_name).all()
    
    result = {}
    for dimension in dimensions:
        category = dimension.category or "Other"
        if category not in result:
            result[category] = []
        result[category].append(dimension.to_dict())
    
    return result