import logging
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple, Union

from flask import current_app
from google.oauth2.service_account import Credentials
from google.oauth2.credentials import Credentials as OAuth2Credentials
from googleapiclient.discovery import build, Resource
from googleapiclient.errors import HttpError

from app.utils.date_utils import date_range_to_ga4_api_format, parse_date_range
from app.models.app_settings import AppSettings

# Check if Google Analytics API is available
try:
    import google.oauth2.service_account
    import google.oauth2.credentials
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
    - Authenticate with GA4 using service account or OAuth2 credentials
    - Fetch properties and streams
    - Run various analytics reports
    - Extract and format metrics and dimensions
    """
    def __init__(self, credentials_path: Optional[str] = None, auth_method: Optional[str] = None):
        """
        Initialize the GA4 Service.
        
        Args:
            credentials_path: Path to the service account credentials JSON file.
                             If None, will use the path from app config.
            auth_method: Authentication method ('service_account' or 'oauth2').
                        If None, will check app settings or default to 'service_account'.
        """
        # Handle non-Flask contexts
        if credentials_path:
            self.credentials_path = credentials_path
        else:
            try:
                from flask import current_app
                self.credentials_path = current_app.config.get('GA4_CREDENTIALS_PATH')
            except RuntimeError:
                # Not in Flask context, use default path
                self.credentials_path = 'credentials/ga4_credentials.json'
        self.scopes = ['https://www.googleapis.com/auth/analytics.readonly']
        self._analytics = None
        self._admin_service = None
        self._data = None
        self._credentials = None
        
        # Determine authentication method
        if auth_method is None:
            # Try to get from database settings
            try:
                from app.models.database import Database
                db = Database()
                self.auth_method = AppSettings.get_setting(db, 'ga4_auth_method', 'service_account')
            except:
                self.auth_method = 'service_account'
        else:
            self.auth_method = auth_method
        
        # Initialize the service if GA4 is available
        if GA4_AVAILABLE:
            if self.auth_method == 'service_account' and self.credentials_path and os.path.exists(self.credentials_path):
                try:
                    self._init_services()
                    logger.info("GA4 Service initialized successfully with service account")
                except Exception as e:
                    logger.error(f"Failed to initialize GA4 Service: {str(e)}", exc_info=True)
            elif self.auth_method == 'oauth2':
                # OAuth2 initialization - try to get credentials from database
                try:
                    from flask import current_app
                    from app.models.app_settings import AppSettings
                    db = current_app.database
                    
                    access_token = AppSettings.get_setting(db, 'oauth2_access_token')
                    refresh_token = AppSettings.get_setting(db, 'oauth2_refresh_token')
                    client_id = AppSettings.get_setting(db, 'oauth2_client_id')
                    client_secret = AppSettings.get_setting(db, 'oauth2_client_secret')
                    
                    if access_token and refresh_token and client_id and client_secret:
                        self._init_oauth2_from_tokens({
                            'access_token': access_token,
                            'refresh_token': refresh_token,
                            'client_id': client_id,
                            'client_secret': client_secret
                        })
                        logger.info("GA4 Service initialized successfully with OAuth2")
                    else:
                        logger.warning("GA4 Service configured for OAuth2 but tokens not found")
                except Exception as e:
                    logger.warning(f"GA4 Service OAuth2 initialization deferred: {e}")
            else:
                logger.warning("GA4 Service not fully initialized: either GA4 libraries not available " 
                              f"or credentials path does not exist: {self.credentials_path}")
    
    def _init_services(self) -> None:
        """Initialize the GA4 API services using appropriate credentials."""
        if not GA4_AVAILABLE:
            logger.warning("Cannot initialize GA4 services: Google Analytics libraries not available")
            return
            
        try:
            if self.auth_method == 'service_account':
                self._credentials = Credentials.from_service_account_file(
                    self.credentials_path, scopes=self.scopes
                )
            elif self.auth_method == 'oauth2':
                # OAuth2 credentials should already be initialized
                if not self._credentials:
                    raise RuntimeError("OAuth2 credentials not initialized. Call _init_oauth2_from_tokens first")
            
            # Initialize the required API services
            # Use v1alpha for admin API as it has better property listing support
            self._admin_service = build('analyticsadmin', 'v1alpha', credentials=self._credentials)
            self._analytics = build('analyticsadmin', 'v1beta', credentials=self._credentials)
            self._data = build('analyticsdata', 'v1beta', credentials=self._credentials)
            
            logger.debug("GA4 API services initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing GA4 API services: {str(e)}", exc_info=True)
            self._admin_service = None
            self._analytics = None
            self._data = None
            self._credentials = None
            raise
    
    def _init_oauth2_from_tokens(self, token_data: Dict[str, Any]) -> None:
        """
        Initialize OAuth2 credentials from stored tokens.
        
        Args:
            token_data: Dictionary containing OAuth2 token information
        """
        if not GA4_AVAILABLE:
            logger.warning("Cannot initialize OAuth2 credentials: Google Analytics libraries not available")
            return
            
        try:
            # Create OAuth2 credentials
            self._credentials = OAuth2Credentials(
                token=token_data.get('access_token'),
                refresh_token=token_data.get('refresh_token'),
                token_uri='https://oauth2.googleapis.com/token',
                client_id=token_data.get('client_id'),
                client_secret=token_data.get('client_secret'),
                scopes=self.scopes
            )
            
            # Initialize the services with OAuth2 credentials
            self._init_services()
            
            logger.debug("GA4 API services initialized with OAuth2 credentials")
        except Exception as e:
            logger.error(f"Error initializing OAuth2 credentials: {str(e)}", exc_info=True)
            raise
    
    def init_oauth2_credentials(self, token_data: Dict[str, Any]) -> None:
        """
        Initialize OAuth2 credentials from token data (legacy method for compatibility).
        
        Args:
            token_data: Dictionary containing OAuth2 token information
        """
        # Add client ID and secret if not in token_data
        if not token_data.get('client_id') or not token_data.get('client_secret'):
            try:
                from flask import current_app
                from app.models.app_settings import AppSettings
                db = current_app.database
                
                token_data['client_id'] = AppSettings.get_setting(db, 'oauth2_client_id')
                token_data['client_secret'] = AppSettings.get_setting(db, 'oauth2_client_secret')
            except Exception as e:
                logger.warning(f"Could not get OAuth2 client config: {e}")
        
        self._init_oauth2_from_tokens(token_data)
    
    def is_available(self) -> bool:
        """
        Check if the GA4 service is available and initialized.
        
        Returns:
            True if the service is available, False otherwise
        """
        return GA4_AVAILABLE and self._analytics is not None and self._data is not None
    
    def list_all_properties_detailed(self) -> List[Dict[str, Any]]:
        """
        List all GA4 properties with detailed information including URLs.
        This method is similar to the old implementation in ga_api.py.
        
        Returns:
            List of property dictionaries with detailed information
        """
        if not self.is_available():
            logger.warning("Cannot list properties: GA4 service not available")
            return []
            
        try:
            properties = []
            page_token = None
            
            # Use the v1alpha admin service to list account summaries
            while True:
                request = self._admin_service.accountSummaries().list()
                if page_token:
                    request = self._admin_service.accountSummaries().list(pageToken=page_token)
                    
                response = request.execute()
                account_summaries = response.get('accountSummaries', [])
                
                for account in account_summaries:
                    account_id = account.get('account', '')
                    account_name = account.get('displayName', '')
                    property_summaries = account.get('propertySummaries', [])
                    
                    logger.debug(f"Processing account: {account_name} ({account_id})")
                    
                    for property_summary in property_summaries:
                        property_resource = property_summary.get('property', '')
                        property_id = property_resource.split('/')[-1] if property_resource else ''
                        
                        # Initialize property data
                        property_data = {
                            'property_id': property_id,
                            'property': property_resource,  # Full resource name
                            'display_name': property_summary.get('displayName', ''),
                            'account': account_id,
                            'account_name': account_name,
                            'website_url': None,
                            'createTime': None,
                            'updateTime': None
                        }
                        
                        # Get website URL from data streams
                        try:
                            # List data streams using v1alpha API
                            streams_request = self._admin_service.properties().dataStreams().list(
                                parent=property_resource
                            )
                            streams_response = streams_request.execute()
                            
                            streams = streams_response.get('dataStreams', [])
                            for stream in streams:
                                # Check if this is a web stream
                                if stream.get('type') == 'WEB_DATA_STREAM':
                                    web_data = stream.get('webStreamData', {})
                                    property_data['website_url'] = web_data.get('defaultUri')
                                    break
                                    
                        except Exception as e:
                            logger.warning(f"Error getting data streams for property {property_resource}: {e}")
                        
                        # Try to get additional property details
                        try:
                            property_details = self._admin_service.properties().get(
                                name=property_resource
                            ).execute()
                            
                            if property_details:
                                property_data['createTime'] = property_details.get('createTime')
                                property_data['updateTime'] = property_details.get('updateTime')
                                property_data['display_name'] = property_details.get('displayName', property_data['display_name'])
                        except Exception as e:
                            logger.warning(f"Could not get property details for {property_resource}: {e}")
                        
                        properties.append(property_data)
                
                # Check for next page
                page_token = response.get('nextPageToken')
                if not page_token:
                    break
                    
            logger.info(f"Found {len(properties)} GA4 properties with details")
            return properties
            
        except Exception as e:
            logger.error(f"Error listing GA4 properties: {str(e)}", exc_info=True)
            return []
    
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
            # Use v1alpha admin service for better property listing
            account_summaries = []
            page_token = None
            
            while True:
                if page_token:
                    response = self._admin_service.accountSummaries().list(pageToken=page_token).execute()
                else:
                    response = self._admin_service.accountSummaries().list().execute()
                
                account_summaries.extend(response.get('accountSummaries', []))
                
                page_token = response.get('nextPageToken')
                if not page_token:
                    break
                    
            return account_summaries
        except HttpError as e:
            logger.error(f"Error listing GA4 account summaries: {str(e)}", exc_info=True)
            return []
    
    def list_properties(self, account_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all GA4 properties, optionally filtered by account ID.
        
        Args:
            account_id: Optional account ID to filter properties by
            
        Returns:
            List of property objects with additional data stream information
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
                property_summaries = summary.get('propertySummaries', [])
                
                for property_summary in property_summaries:
                    property_obj = property_summary.copy()
                    
                    # Try to get additional information from data streams
                    property_id = property_summary.get('property', '').split('/')[-1]
                    if property_id:
                        try:
                            # Get data streams to find website URL
                            streams = self.list_streams(property_id)
                            for stream in streams:
                                # Check for web stream data
                                if stream.get('type') == 'WEB_DATA_STREAM' and stream.get('webStreamData'):
                                    property_obj['website_url'] = stream['webStreamData'].get('defaultUri')
                                    break
                        except Exception as e:
                            logger.warning(f"Could not get streams for property {property_id}: {e}")
                    
                    properties.append(property_obj)
                
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
    
    def run_report(self, property_id: str, metrics: List[str], dimensions: List[str] = None,
                   date_range: str = "last_30_days", limit: int = 100) -> Dict[str, Any]:
        """
        Run a report for a specific GA4 property.
        
        Args:
            property_id: The GA4 property ID
            metrics: List of metric names (e.g., ['activeUsers', 'screenPageViews'])
            dimensions: List of dimension names (e.g., ['pagePath', 'country'])
            date_range: Date range string or custom range
            limit: Maximum number of rows to return
            
        Returns:
            Report response from the API
        """
        if not self.is_available():
            logger.warning("Cannot run report: GA4 service not available")
            return {}
            
        try:
            # Convert date range to API format
            start_date, end_date = parse_date_range(date_range)
            date_ranges = [date_range_to_ga4_api_format(start_date, end_date)]
            
            # Build metrics list
            metrics_list = [{'name': metric} for metric in metrics]
            
            # Build dimensions list if provided
            dimensions_list = []
            if dimensions:
                dimensions_list = [{'name': dimension} for dimension in dimensions]
            
            # Create the report request
            request_body = {
                'dateRanges': date_ranges,
                'metrics': metrics_list,
                'limit': limit
            }
            
            if dimensions_list:
                request_body['dimensions'] = dimensions_list
            
            # Run the report
            response = self._data.properties().runReport(
                property=f"properties/{property_id}",
                body=request_body
            ).execute()
            
            logger.debug(f"Report executed successfully for property {property_id}")
            return response
            
        except HttpError as e:
            logger.error(f"Error running report for property {property_id}: {str(e)}", exc_info=True)
            return {}
    
    def get_realtime_report(self, property_id: str, metrics: List[str], dimensions: List[str] = None,
                           limit: int = 100) -> Dict[str, Any]:
        """
        Get real-time data for a GA4 property.
        
        Args:
            property_id: The GA4 property ID
            metrics: List of metric names
            dimensions: List of dimension names
            limit: Maximum number of rows to return
            
        Returns:
            Real-time report response
        """
        if not self.is_available():
            logger.warning("Cannot get realtime report: GA4 service not available")
            return {}
            
        try:
            # Build metrics and dimensions
            metrics_list = [{'name': metric} for metric in metrics]
            dimensions_list = [{'name': dimension} for dimension in dimensions] if dimensions else []
            
            # Create the request body
            request_body = {
                'metrics': metrics_list,
                'limit': limit
            }
            
            if dimensions_list:
                request_body['dimensions'] = dimensions_list
            
            # Run the realtime report
            response = self._data.properties().runRealtimeReport(
                property=f"properties/{property_id}",
                body=request_body
            ).execute()
            
            logger.debug(f"Realtime report executed successfully for property {property_id}")
            return response
            
        except HttpError as e:
            logger.error(f"Error getting realtime report for property {property_id}: {str(e)}", exc_info=True)
            return {}
    
    def batch_run_reports(self, property_id: str, requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Run multiple reports in a single batch request.
        
        Args:
            property_id: The GA4 property ID
            requests: List of report request configurations
            
        Returns:
            List of report responses
        """
        if not self.is_available():
            logger.warning("Cannot batch run reports: GA4 service not available")
            return []
            
        try:
            # Convert each request to the proper format
            formatted_requests = []
            for request in requests:
                date_range = request.get('date_range', 'last_30_days')
                start_date, end_date = parse_date_range(date_range)
                
                formatted_request = {
                    'dateRanges': [date_range_to_ga4_api_format(start_date, end_date)],
                    'metrics': [{'name': metric} for metric in request.get('metrics', [])],
                    'limit': request.get('limit', 100)
                }
                
                if 'dimensions' in request:
                    formatted_request['dimensions'] = [{'name': dim} for dim in request['dimensions']]
                
                formatted_requests.append(formatted_request)
            
            # Run the batch report
            response = self._data.properties().batchRunReports(
                property=f"properties/{property_id}",
                body={'requests': formatted_requests}
            ).execute()
            
            logger.debug(f"Batch report executed successfully for property {property_id}")
            return response.get('reports', [])
            
        except HttpError as e:
            logger.error(f"Error running batch reports for property {property_id}: {str(e)}", exc_info=True)
            return []
    
    def get_metadata(self, property_id: str) -> Dict[str, Any]:
        """
        Get metadata about available metrics and dimensions for a property.
        
        Args:
            property_id: The GA4 property ID
            
        Returns:
            Metadata response containing available metrics and dimensions
        """
        if not self.is_available():
            logger.warning("Cannot get metadata: GA4 service not available")
            return {}
            
        try:
            response = self._data.properties().getMetadata(
                name=f"properties/{property_id}/metadata"
            ).execute()
            
            logger.debug(f"Metadata retrieved successfully for property {property_id}")
            return response
            
        except HttpError as e:
            logger.error(f"Error getting metadata for property {property_id}: {str(e)}", exc_info=True)
            return {}