import logging
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple, Union

from flask import current_app
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build, Resource
from googleapiclient.errors import HttpError

from app.utils.date_utils import format_date_for_ga4, parse_date_range

# Check if Google Analytics API is available
try:
    import google.oauth2.service_account
    import googleapiclient.discovery
    import googleapiclient.errors
    GA4_AVAILABLE = True
except ImportError:
    GA4_AVAILABLE = False
    logging.warning("Google Analytics libraries not available. GA4 functionality will be limited.")

logger = logging.getLogger(__name__)

class GA4Service:
    """
    Service for interfacing with Google Analytics 4 API.
    
    This service provides methods to:
    - Authenticate with GA4 using service account credentials
    - Fetch properties and streams
    - Run various analytics reports
    - Extract and format metrics and dimensions
    """
    def __init__(self, credentials_path: Optional[str] = None):
        """
        Initialize the GA4 Service.
        
        Args:
            credentials_path: Path to the service account credentials JSON file.
                             If None, will use the path from app config.
        """
        self.credentials_path = credentials_path or current_app.config.get('GA4_CREDENTIALS_PATH')
        self.scopes = ['https://www.googleapis.com/auth/analytics.readonly']
        self._analytics = None
        self._admin = None
        self._data = None
        self._credentials = None
        
        # Initialize the service if GA4 is available
        if GA4_AVAILABLE and self.credentials_path and os.path.exists(self.credentials_path):
            try:
                self._init_services()
                logger.info("GA4 Service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize GA4 Service: {str(e)}", exc_info=True)
        else:
            logger.warning("GA4 Service not fully initialized: either GA4 libraries not available " 
                          f"or credentials path does not exist: {self.credentials_path}")
    
    def _init_services(self) -> None:
        """Initialize the GA4 API services using service account credentials."""
        if not GA4_AVAILABLE:
            logger.warning("Cannot initialize GA4 services: Google Analytics libraries not available")
            return
            
        try:
            self._credentials = Credentials.from_service_account_file(
                self.credentials_path, scopes=self.scopes
            )
            
            # Initialize the required API services
            self._analytics = build('analyticsadmin', 'v1beta', credentials=self._credentials)
            self._admin = self._analytics.accountSummaries()
            self._data = build('analyticsdata', 'v1beta', credentials=self._credentials)
            
            logger.debug("GA4 API services initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing GA4 API services: {str(e)}", exc_info=True)
            self._analytics = None
            self._admin = None
            self._data = None
            self._credentials = None
            raise
    
    def is_available(self) -> bool:
        """
        Check if the GA4 service is available and initialized.
        
        Returns:
            True if the service is available, False otherwise
        """
        return GA4_AVAILABLE and self._analytics is not None and self._data is not None
    
    def list_account_summaries(self) -> List[Dict[str, Any]]:
        """
        List all available GA4 account summaries.
        
        Returns:
            List of account summary objects
        """
        if not self.is_available():
            logger.warning("Cannot list account summaries: GA4 service not available")
            return []
            
        try:
            result = self._admin.list().execute()
            return result.get('accountSummaries', [])
        except HttpError as e:
            logger.error(f"Error listing GA4 account summaries: {str(e)}", exc_info=True)
            return []
    
    def list_properties(self, account_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all GA4 properties, optionally filtered by account ID.
        
        Args:
            account_id: Optional account ID to filter properties by
            
        Returns:
            List of property objects
        """
        if not self.is_available():
            logger.warning("Cannot list properties: GA4 service not available")
            return []
            
        properties = []
        
        try:
            # Get all account summaries
            account_summaries = self.list_account_summaries()
            
            # Filter by account_id if provided
            if account_id:
                account_summaries = [
                    summary for summary in account_summaries 
                    if summary.get('account') == f"accounts/{account_id}"
                ]
            
            # Extract properties from account summaries
            for summary in account_summaries:
                properties.extend(summary.get('propertySummaries', []))
                
            logger.debug(f"Found {len(properties)} GA4 properties")
            return properties
        except Exception as e:
            logger.error(f"Error listing GA4 properties: {str(e)}", exc_info=True)
            return []
    
    def get_property(self, property_id: str) -> Optional[Dict[str, Any]]:
        """
        Get details for a specific GA4 property.
        
        Args:
            property_id: The GA4 property ID
            
        Returns:
            Property details if found, None otherwise
        """
        if not self.is_available():
            logger.warning("Cannot get property: GA4 service not available")
            return None
            
        try:
            property_path = f"properties/{property_id}"
            return self._analytics.properties().get(name=property_path).execute()
        except HttpError as e:
            logger.error(f"Error getting GA4 property {property_id}: {str(e)}", exc_info=True)
            return None
    
    def list_streams(self, property_id: str) -> List[Dict[str, Any]]:
        """
        List all data streams for a GA4 property.
        
        Args:
            property_id: The GA4 property ID
            
        Returns:
            List of data stream objects
        """
        if not self.is_available():
            logger.warning("Cannot list streams: GA4 service not available")
            return []
            
        try:
            property_path = f"properties/{property_id}"
            result = self._analytics.properties().dataStreams().list(parent=property_path).execute()
            return result.get('dataStreams', [])
        except HttpError as e:
            logger.error(f"Error listing streams for property {property_id}: {str(e)}", exc_info=True)
            return []
    
    def get_stream(self, property_id: str, stream_id: str) -> Optional[Dict[str, Any]]:
        """
        Get details for a specific data stream.
        
        Args:
            property_id: The GA4 property ID
            stream_id: The stream ID
            
        Returns:
            Stream details if found, None otherwise
        """
        if not self.is_available():
            logger.warning("Cannot get stream: GA4 service not available")
            return None
            
        try:
            stream_path = f"properties/{property_id}/dataStreams/{stream_id}"
            return self._analytics.properties().dataStreams().get(name=stream_path).execute()
        except HttpError as e:
            logger.error(f"Error getting stream {stream_id} for property {property_id}: {str(e)}", exc_info=True)
            return None
    
    def run_report(self, 
                   property_id: str,
                   start_date: Union[str, datetime],
                   end_date: Union[str, datetime],
                   metrics: List[str],
                   dimensions: Optional[List[str]] = None,
                   filters: Optional[Dict[str, Any]] = None,
                   limit: int = 10000) -> Dict[str, Any]:
        """
        Run a GA4 report with the specified parameters.
        
        Args:
            property_id: The GA4 property ID
            start_date: Start date (YYYY-MM-DD or datetime)
            end_date: End date (YYYY-MM-DD or datetime)
            metrics: List of metric names to include
            dimensions: List of dimension names to include
            filters: Dictionary of dimension/metric filters
            limit: Maximum number of rows to return
            
        Returns:
            Dictionary containing the report results
        """
        if not self.is_available():
            logger.warning("Cannot run report: GA4 service not available")
            return {'rows': [], 'metadata': {'status': 'error', 'message': 'GA4 service not available'}}
            
        try:
            # Format dates for GA4
            start_date_str = format_date_for_ga4(start_date)
            end_date_str = format_date_for_ga4(end_date)
            
            # Prepare metrics and dimensions
            metric_params = [{'name': m} for m in metrics]
            dimension_params = [{'name': d} for d in (dimensions or [])]
            
            # Prepare report request
            request = {
                'dateRanges': [{'startDate': start_date_str, 'endDate': end_date_str}],
                'metrics': metric_params,
                'dimensions': dimension_params,
                'limit': limit
            }
            
            # Add dimension filter if provided
            if filters:
                request['dimensionFilter'] = filters
            
            # Execute the report
            property_path = f"properties/{property_id}"
            response = self._data.properties().runReport(
                property=property_path,
                body=request
            ).execute()
            
            logger.debug(f"Successfully ran GA4 report for property {property_id} with {len(response.get('rows', []))} rows")
            return response
        except Exception as e:
            logger.error(f"Error running GA4 report for property {property_id}: {str(e)}", exc_info=True)
            return {'rows': [], 'metadata': {'status': 'error', 'message': str(e)}}
    
    def get_traffic_report(self,
                           property_id: str,
                           date_range: str,
                           metrics: Optional[List[str]] = None,
                           dimensions: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get a traffic analysis report for a property.
        
        Args:
            property_id: The GA4 property ID
            date_range: Date range string (e.g., 'last7days', '30daysAgo')
            metrics: List of traffic metrics to include
            dimensions: List of dimensions to include
            
        Returns:
            Dictionary containing the report results
        """
        # Default metrics and dimensions if not provided
        if metrics is None:
            metrics = [
                'totalUsers', 
                'newUsers', 
                'sessions', 
                'screenPageViews',
                'averageSessionDuration'
            ]
            
        if dimensions is None:
            dimensions = ['date']
            
        # Parse date range
        start_date, end_date = parse_date_range(date_range)
        
        # Run the report
        return self.run_report(
            property_id=property_id,
            start_date=start_date,
            end_date=end_date,
            metrics=metrics,
            dimensions=dimensions
        )
    
    def get_engagement_report(self,
                              property_id: str,
                              date_range: str) -> Dict[str, Any]:
        """
        Get an engagement report for a property.
        
        Args:
            property_id: The GA4 property ID
            date_range: Date range string (e.g., 'last7days', '30daysAgo')
            
        Returns:
            Dictionary containing the report results
        """
        # Define metrics and dimensions for engagement report
        metrics = [
            'engagementRate',
            'userEngagementDuration',
            'averageSessionDuration',
            'bounceRate',
            'screenPageViewsPerSession'
        ]
        
        dimensions = ['date']
        
        # Parse date range
        start_date, end_date = parse_date_range(date_range)
        
        # Run the report
        return self.run_report(
            property_id=property_id,
            start_date=start_date,
            end_date=end_date,
            metrics=metrics,
            dimensions=dimensions
        )
    
    def get_page_analysis_report(self,
                                 property_id: str,
                                 date_range: str,
                                 limit: int = 20) -> Dict[str, Any]:
        """
        Get a page analysis report for a property.
        
        Args:
            property_id: The GA4 property ID
            date_range: Date range string (e.g., 'last7days', '30daysAgo')
            limit: Maximum number of pages to include
            
        Returns:
            Dictionary containing the report results
        """
        # Define metrics and dimensions for page analysis
        metrics = [
            'screenPageViews',
            'averageSessionDuration',
            'bounceRate',
            'engagementRate'
        ]
        
        dimensions = ['pagePath']
        
        # Parse date range
        start_date, end_date = parse_date_range(date_range)
        
        # Run the report
        return self.run_report(
            property_id=property_id,
            start_date=start_date,
            end_date=end_date,
            metrics=metrics,
            dimensions=dimensions,
            limit=limit
        )
    
    def format_report_data(self, report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Format raw GA4 report data into a more usable structure.
        
        Args:
            report: Raw GA4 report data
            
        Returns:
            List of formatted data rows
        """
        if not report or 'rows' not in report:
            return []
            
        formatted_data = []
        
        # Extract dimension and metric headers
        dimension_headers = [h.get('name') for h in report.get('dimensionHeaders', [])]
        metric_headers = [h.get('name') for h in report.get('metricHeaders', [])]
        
        # Process each row
        for row in report.get('rows', []):
            data_row = {}
            
            # Add dimensions
            for i, dim in enumerate(row.get('dimensionValues', [])):
                if i < len(dimension_headers):
                    data_row[dimension_headers[i]] = dim.get('value')
            
            # Add metrics
            for i, metric in enumerate(row.get('metricValues', [])):
                if i < len(metric_headers):
                    data_row[metric_headers[i]] = metric.get('value')
            
            formatted_data.append(data_row)
        
        return formatted_data
    
    def get_realtime_users(self, property_id: str) -> int:
        """
        Get the current number of active users for a property.
        
        Args:
            property_id: The GA4 property ID
            
        Returns:
            Number of active users, or 0 if an error occurs
        """
        if not self.is_available():
            logger.warning("Cannot get realtime users: GA4 service not available")
            return 0
            
        try:
            # Run a realtime report with activeUsers metric
            property_path = f"properties/{property_id}"
            response = self._data.properties().runRealtimeReport(
                property=property_path,
                body={
                    'metrics': [{'name': 'activeUsers'}]
                }
            ).execute()
            
            # Extract active users count
            if 'rows' in response and len(response['rows']) > 0:
                return int(response['rows'][0]['metricValues'][0]['value'])
            
            return 0
        except Exception as e:
            logger.error(f"Error getting realtime users for property {property_id}: {str(e)}", exc_info=True)
            return 0