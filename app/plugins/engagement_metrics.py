import logging
from typing import Dict, Any, List, Optional

from app.plugins.base_plugin import BasePlugin
from app.services import get_service

logger = logging.getLogger(__name__)

class EngagementMetricsPlugin(BasePlugin):
    """
    Plugin for analyzing and visualizing engagement metrics from GA4.
    
    This plugin processes raw GA4 data to calculate and visualize key engagement
    metrics such as bounce rate, session duration, and page views per session.
    """
    
    # Plugin metadata
    PLUGIN_ID = "engagement_metrics"
    PLUGIN_NAME = "Engagement Metrics"
    PLUGIN_VERSION = "1.0.0"
    PLUGIN_DESCRIPTION = "Analyzes and visualizes engagement metrics from GA4 data"
    PLUGIN_AUTHOR = "GA4 Analytics Dashboard"
    PLUGIN_CATEGORY = "Analytics"
    
    def __init__(self):
        """Initialize the Engagement Metrics plugin."""
        super().__init__()
    
    def get_default_config(self) -> Dict[str, Any]:
        """
        Get the default configuration for this plugin.
        
        Returns:
            Dictionary of default configuration parameters
        """
        return {
            "metrics": [
                "engagementRate",
                "userEngagementDuration",
                "averageSessionDuration",
                "bounceRate",
                "screenPageViewsPerSession"
            ],
            "dimensions": ["date"],
            "time_period": "last30days",
            "chart_type": "line",
            "display_tables": True
        }
    
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """
        Validate the provided configuration.
        
        Args:
            config: Dictionary of configuration parameters to validate
            
        Returns:
            List of error messages (empty if configuration is valid)
        """
        errors = []
        
        # Check metrics
        if "metrics" not in config or not config["metrics"]:
            errors.append("At least one metric must be specified")
        
        # Check dimensions
        if "dimensions" not in config or not config["dimensions"]:
            errors.append("At least one dimension must be specified")
        
        # Check time period
        valid_time_periods = [
            "today", "yesterday", "7daysAgo", "last7days", 
            "30daysAgo", "last30days", "last90days", "last365days"
        ]
        if "time_period" not in config or config["time_period"] not in valid_time_periods:
            errors.append(f"Time period must be one of: {', '.join(valid_time_periods)}")
        
        # Check chart type
        valid_chart_types = ["line", "bar", "pie", "table"]
        if "chart_type" not in config or config["chart_type"] not in valid_chart_types:
            errors.append(f"Chart type must be one of: {', '.join(valid_chart_types)}")
        
        return errors
    
    def process_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process engagement metrics data from GA4.
        
        Args:
            data: Dictionary containing:
                - property_id: GA4 property ID
                - date_range: Date range string (e.g., 'last30days')
                - metrics: Optional list of metrics to include
                - dimensions: Optional list of dimensions to include
                
        Returns:
            Dictionary containing processed engagement metrics and visualizations
        """
        logger.debug(f"Processing engagement metrics for property {data.get('property_id')}")
        
        # Get the GA4 service
        ga4_service = get_service('ga4')
        if not ga4_service:
            logger.error("GA4 service not available")
            return {"error": "GA4 service not available"}
        
        # Check if GA4 service is available
        if not ga4_service.is_available():
            logger.error("GA4 service is not properly initialized or credentials are missing")
            return {"error": "GA4 service is not available. Check your credentials."}
        
        # Get property ID
        property_id = data.get('property_id')
        if not property_id:
            logger.error("No property ID provided")
            return {"error": "Property ID is required"}
        
        # Get date range
        date_range = data.get('date_range', self.config.get('time_period', 'last30days'))
        
        # Get metrics and dimensions
        metrics = data.get('metrics', self.config.get('metrics'))
        dimensions = data.get('dimensions', self.config.get('dimensions'))
        
        try:
            # Run the engagement report
            report = ga4_service.run_report(
                property_id=property_id,
                start_date=date_range,
                end_date='today',
                metrics=metrics,
                dimensions=dimensions
            )
            
            # Format the data
            formatted_data = ga4_service.format_report_data(report)
            
            # Calculate additional metrics
            result = self._calculate_additional_metrics(formatted_data)
            
            # Add visualizations config
            result['visualizations'] = self._generate_visualizations(formatted_data)
            
            # Add metadata
            result['metadata'] = {
                'property_id': property_id,
                'date_range': date_range,
                'metrics': metrics,
                'dimensions': dimensions,
                'generated_at': ga4_service._format_datetime_for_display(),
                'plugin_info': self.get_info()
            }
            
            logger.info(f"Successfully processed engagement metrics for {property_id}")
            return result
        
        except Exception as e:
            logger.error(f"Error processing engagement metrics: {str(e)}", exc_info=True)
            return {"error": f"Failed to process engagement metrics: {str(e)}"}
    
    def _calculate_additional_metrics(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate additional engagement metrics from the raw data.
        
        Args:
            data: List of data points from GA4
            
        Returns:
            Dictionary containing:
            - raw_data: The original formatted data
            - summary: Summary metrics
            - trends: Trend analysis
        """
        if not data:
            return {
                'raw_data': [],
                'summary': {},
                'trends': {}
            }
        
        # Get the raw data
        result = {
            'raw_data': data,
            'summary': {},
            'trends': {}
        }
        
        # Calculate averages for summary
        numeric_fields = {}
        for row in data:
            for key, value in row.items():
                if key != 'date' and key != 'dateRange':
                    try:
                        numeric_value = float(value)
                        if key not in numeric_fields:
                            numeric_fields[key] = []
                        numeric_fields[key].append(numeric_value)
                    except (ValueError, TypeError):
                        pass
        
        # Calculate averages
        for key, values in numeric_fields.items():
            if values:
                result['summary'][f'avg_{key}'] = sum(values) / len(values)
                result['summary'][f'min_{key}'] = min(values)
                result['summary'][f'max_{key}'] = max(values)
        
        # Calculate simple trends (compare first and last values)
        if len(data) >= 2:
            for key in numeric_fields:
                first_value = float(data[0].get(key, 0))
                last_value = float(data[-1].get(key, 0))
                
                if first_value > 0:
                    percent_change = ((last_value - first_value) / first_value) * 100
                    result['trends'][key] = {
                        'first_value': first_value,
                        'last_value': last_value,
                        'change': last_value - first_value,
                        'percent_change': percent_change,
                        'direction': 'up' if percent_change > 0 else 'down' if percent_change < 0 else 'flat'
                    }
        
        return result
    
    def _generate_visualizations(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate visualization configurations for the processed data.
        
        Args:
            data: List of data points from GA4
            
        Returns:
            Dictionary containing visualization configurations
        """
        chart_type = self.config.get('chart_type', 'line')
        
        # Create a basic visualization config
        visualizations = {
            'primary_chart': {
                'type': chart_type,
                'title': 'Engagement Metrics Over Time',
                'x_axis': 'date',
                'y_axis': 'value',
                'series': []
            },
            'tables': []
        }
        
        # Extract series data for charts
        if data and len(data) > 0:
            metrics = [key for key in data[0].keys() if key != 'date' and key != 'dateRange']
            
            for metric in metrics:
                series = {
                    'name': metric,
                    'data': [
                        {'x': row.get('date', ''), 'y': float(row.get(metric, 0))} 
                        for row in data
                    ]
                }
                visualizations['primary_chart']['series'].append(series)
                
            # Add table visualization
            if self.config.get('display_tables', True):
                visualizations['tables'].append({
                    'title': 'Engagement Metrics by Day',
                    'columns': ['date'] + metrics,
                    'data': data
                })
        
        return visualizations
        
    def get_required_permissions(self) -> List[str]:
        """
        Get the list of permissions required by this plugin.
        
        Returns:
            List of permission strings
        """
        return ['ga4:read']
    
    def get_templates(self) -> Dict[str, str]:
        """
        Get templates provided by this plugin.
        
        Returns:
            Dictionary mapping template names to template paths
        """
        return {
            'engagement_dashboard': 'plugins/engagement_metrics/dashboard.html',
            'engagement_report': 'plugins/engagement_metrics/report.html',
        }
    
    def get_scripts(self) -> List[str]:
        """
        Get JavaScript files provided by this plugin.
        
        Returns:
            List of JavaScript file paths
        """
        return [
            'plugins/engagement_metrics/js/charts.js',
            'plugins/engagement_metrics/js/engagement.js',
        ]
    
    def get_styles(self) -> List[str]:
        """
        Get CSS files provided by this plugin.
        
        Returns:
            List of CSS file paths
        """
        return [
            'plugins/engagement_metrics/css/engagement.css',
        ]