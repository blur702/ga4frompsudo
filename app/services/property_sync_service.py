"""
Property Sync Service for GA4 Analytics Dashboard.

This service handles fetching and synchronizing GA4 properties
and their associated websites/data streams from the Google Analytics API
to the local database.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from app.services.ga4_service import GA4Service
from app.models.property import Property
from app.models.website import Website
from app.models.database import Database

logger = logging.getLogger(__name__)


class PropertySyncService:
    """Service for synchronizing GA4 properties and websites to the database."""
    
    def __init__(self, database: Database, ga4_service: GA4Service):
        """
        Initialize the PropertySyncService.
        
        Args:
            database: Database instance for storing properties and websites
            ga4_service: GA4Service instance for API access
        """
        self.database = database
        self.ga4_service = ga4_service
    
    def sync_all_properties(self, 
                           fetch_websites: bool = True,
                           update_existing: bool = True) -> Dict[str, Any]:
        """
        Fetch all GA4 properties and optionally their websites, and sync to database.
        Uses the improved method from the old implementation.
        
        Args:
            fetch_websites: Whether to also fetch and sync websites/data streams
            update_existing: Whether to update existing records or skip them
            
        Returns:
            Dictionary with sync results:
                - properties_fetched: Number of properties fetched from API
                - properties_created: Number of new properties created
                - properties_updated: Number of properties updated
                - websites_fetched: Number of websites fetched
                - websites_created: Number of new websites created
                - websites_updated: Number of websites updated
                - errors: List of any errors encountered
        """
        logger.info("Starting property sync operation")
        
        results = {
            'properties_fetched': 0,
            'properties_created': 0,
            'properties_updated': 0,
            'websites_fetched': 0,
            'websites_created': 0,
            'websites_updated': 0,
            'errors': []
        }
        
        try:
            # First try the simpler list_properties method for OAuth2
            if self.ga4_service.auth_method == 'oauth2':
                logger.info("Using OAuth2 - fetching properties with list_properties()")
                properties_data = []
                
                # Get account summaries and properties
                account_summaries = self.ga4_service.list_account_summaries()
                for account in account_summaries:
                    account_id = account.get('account', '')
                    account_name = account.get('displayName', '')
                    property_summaries = account.get('propertySummaries', [])
                    
                    for prop_summary in property_summaries:
                        property_resource = prop_summary.get('property', '')
                        property_id = property_resource.split('/')[-1] if property_resource else ''
                        
                        property_data = {
                            'property_id': property_id,
                            'property': property_resource,
                            'display_name': prop_summary.get('displayName', ''),
                            'displayName': prop_summary.get('displayName', ''),  # Alternative key
                            'account': account_id,
                            'account_name': account_name,
                            'website_url': None,  # Will be fetched separately if needed
                            'createTime': None,
                            'updateTime': None
                        }
                        properties_data.append(property_data)
                        
                results['properties_fetched'] = len(properties_data)
            else:
                # Use the detailed method for service account
                properties_data = self.ga4_service.list_all_properties_detailed()
                results['properties_fetched'] = len(properties_data)
            
            logger.info(f"Fetched {len(properties_data)} properties from GA4")
            
            for prop_data in properties_data:
                try:
                    property_id = prop_data.get('property_id', '')
                    property_resource = prop_data.get('property', '')
                    account_id = prop_data.get('account', '').split('/')[-1]
                    
                    if not property_id:
                        logger.warning(f"Property without ID found: {prop_data}")
                        continue
                    
                    # Sync property to database
                    created, updated = self._sync_property(
                        property_id=property_id,
                        property_details=prop_data,
                        account_id=account_id,
                        update_existing=update_existing
                    )
                    
                    if created:
                        results['properties_created'] += 1
                    elif updated:
                        results['properties_updated'] += 1
                    
                    # If website URL is already in the property data, create/update website record
                    if fetch_websites and prop_data.get('website_url'):
                        try:
                            # Get the property from database to get its ID
                            property_obj = Property.find_by_ga4_property_id(
                                self.database,
                                property_resource
                            )
                            
                            if property_obj:
                                # Create a mock stream ID for the website
                                stream_id = f"{property_resource}/dataStreams/web"
                                
                                created_web, updated_web = self._sync_website(
                                    stream_id=stream_id,
                                    property_db_id=property_obj.id,
                                    website_url=prop_data['website_url'],
                                    stream_details={'createTime': prop_data.get('createTime'),
                                                   'updateTime': prop_data.get('updateTime')},
                                    update_existing=update_existing
                                )
                                
                                results['websites_fetched'] += 1
                                if created_web:
                                    results['websites_created'] += 1
                                elif updated_web:
                                    results['websites_updated'] += 1
                        except Exception as e:
                            error_msg = f"Error syncing website for property {property_id}: {str(e)}"
                            logger.error(error_msg, exc_info=True)
                            results['errors'].append(error_msg)
                                    
                except Exception as e:
                    error_msg = f"Error processing property data: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    results['errors'].append(error_msg)
                        
        except Exception as e:
            error_msg = f"Error fetching properties: {str(e)}"
            logger.error(error_msg, exc_info=True)
            results['errors'].append(error_msg)
        
        logger.info(f"Property sync completed. Results: {results}")
        return results
    
    def sync_single_property(self, 
                           property_id: str,
                           fetch_websites: bool = True,
                           update_existing: bool = True) -> Dict[str, Any]:
        """
        Sync a single GA4 property and optionally its websites.
        
        Args:
            property_id: The GA4 property ID (numeric part only)
            fetch_websites: Whether to also fetch and sync websites/data streams
            update_existing: Whether to update existing records or skip them
            
        Returns:
            Dictionary with sync results similar to sync_all_properties()
        """
        logger.info(f"Syncing single property: {property_id}")
        
        results = {
            'properties_fetched': 0,
            'properties_created': 0,
            'properties_updated': 0,
            'websites_fetched': 0,
            'websites_created': 0,
            'websites_updated': 0,
            'errors': []
        }
        
        try:
            # Get property details
            property_details = self.ga4_service.get_property(property_id)
            
            if property_details:
                results['properties_fetched'] = 1
                
                # Extract account ID from property details
                account_id = property_details.get('parent', '').split('/')[-1]
                
                # Sync property to database
                created, updated = self._sync_property(
                    property_id=property_id,
                    property_details=property_details,
                    account_id=account_id,
                    update_existing=update_existing
                )
                
                if created:
                    results['properties_created'] = 1
                elif updated:
                    results['properties_updated'] = 1
                
                # Fetch websites if requested
                if fetch_websites:
                    website_results = self._sync_websites_for_property(
                        property_id=property_id,
                        update_existing=update_existing
                    )
                    
                    results['websites_fetched'] = website_results['fetched']
                    results['websites_created'] = website_results['created']
                    results['websites_updated'] = website_results['updated']
                    
                    if website_results['errors']:
                        results['errors'].extend(website_results['errors'])
            else:
                error_msg = f"Property {property_id} not found in GA4"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                
        except Exception as e:
            error_msg = f"Error syncing property {property_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            results['errors'].append(error_msg)
        
        return results
    
    def _sync_property(self, 
                      property_id: str,
                      property_details: Dict[str, Any],
                      account_id: str,
                      update_existing: bool = True) -> Tuple[bool, bool]:
        """
        Sync a single property to the database.
        
        Args:
            property_id: The GA4 property ID (numeric part only)
            property_details: Property details from GA4 API
            account_id: The account ID this property belongs to
            update_existing: Whether to update existing records
            
        Returns:
            Tuple of (created, updated) booleans
        """
        created = False
        updated = False
        
        try:
            # Get the full property resource name - it might already be in the details
            property_resource = property_details.get('property', f"properties/{property_id}")
            
            # Check if property already exists
            existing_property = Property.find_by_ga4_property_id(
                self.database, 
                property_resource
            )
            
            # Get the display name from the details or use the mapped name
            display_name = property_details.get('display_name') or property_details.get('displayName')
            
            if existing_property:
                if update_existing:
                    # Update existing property
                    existing_property.property_name = display_name
                    existing_property.account_id = account_id
                    # Convert ISO string to datetime if present
                    update_time_str = property_details.get('updateTime')
                    if update_time_str:
                        existing_property.update_time = self._parse_iso_datetime(update_time_str)
                    existing_property.save()
                    updated = True
                    logger.info(f"Updated property: {existing_property.property_name}")
                else:
                    logger.info(f"Skipping existing property: {existing_property.property_name}")
            else:
                # Create new property
                # Convert ISO strings to datetime if present
                create_time_str = property_details.get('createTime')
                update_time_str = property_details.get('updateTime')
                
                new_property = Property(
                    database=self.database,
                    property_id=property_resource,
                    property_name=display_name,
                    account_id=account_id,
                    create_time=self._parse_iso_datetime(create_time_str) if create_time_str else None,
                    update_time=self._parse_iso_datetime(update_time_str) if update_time_str else None
                )
                new_property.save()
                created = True
                logger.info(f"Created property: {new_property.property_name}")
                
        except Exception as e:
            logger.error(f"Error syncing property {property_id}: {str(e)}", exc_info=True)
            raise
        
        return created, updated
    
    def _parse_iso_datetime(self, datetime_str: str) -> Optional[datetime]:
        """Parse ISO 8601 datetime string to datetime object."""
        if not datetime_str:
            return None
        try:
            from dateutil import parser
            return parser.isoparse(datetime_str)
        except Exception:
            try:
                # Fallback for standard ISO format
                return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            except Exception as e:
                logger.warning(f"Could not parse datetime string: {datetime_str}, error: {e}")
                return None
    
    def _sync_websites_for_property(self,
                                  property_id: str,
                                  update_existing: bool = True) -> Dict[str, Any]:
        """
        Sync all websites/data streams for a property.
        
        Args:
            property_id: The GA4 property ID
            update_existing: Whether to update existing records
            
        Returns:
            Dictionary with website sync results
        """
        results = {
            'fetched': 0,
            'created': 0,
            'updated': 0,
            'errors': []
        }
        
        try:
            # Get the property from database
            property_obj = Property.find_by_ga4_property_id(
                self.database,
                f"properties/{property_id}"
            )
            
            if not property_obj:
                error_msg = f"Property {property_id} not found in database"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                return results
            
            # Fetch data streams from GA4
            streams = self.ga4_service.list_streams(property_id)
            results['fetched'] = len(streams)
            
            for stream in streams:
                try:
                    stream_id = stream.get('name', '').split('/')[-1]
                    
                    # Get full stream details
                    stream_details = self.ga4_service.get_stream(property_id, stream_id)
                    
                    if stream_details:
                        # Only process web streams
                        if stream_details.get('type') == 'WEB_DATA_STREAM':
                            web_stream_data = stream_details.get('webStreamData', {})
                            
                            created, updated = self._sync_website(
                                stream_id=stream.get('name'),
                                property_db_id=property_obj.id,
                                website_url=web_stream_data.get('defaultUri'),
                                stream_details=stream_details,
                                update_existing=update_existing
                            )
                            
                            if created:
                                results['created'] += 1
                            elif updated:
                                results['updated'] += 1
                                
                except Exception as e:
                    error_msg = f"Error syncing stream {stream_id}: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    results['errors'].append(error_msg)
                    
        except Exception as e:
            error_msg = f"Error fetching streams for property {property_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            results['errors'].append(error_msg)
        
        return results
    
    def _sync_website(self,
                     stream_id: str,
                     property_db_id: int,
                     website_url: str,
                     stream_details: Dict[str, Any],
                     update_existing: bool = True) -> Tuple[bool, bool]:
        """
        Sync a single website/data stream to the database.
        
        Args:
            stream_id: The full GA4 data stream ID
            property_db_id: The database ID of the parent property
            website_url: The website URL
            stream_details: Stream details from GA4 API
            update_existing: Whether to update existing records
            
        Returns:
            Tuple of (created, updated) booleans
        """
        created = False
        updated = False
        
        try:
            # Check if website already exists
            existing_website = Website.find_by_ga4_website_id(self.database, stream_id)
            
            if existing_website:
                if update_existing:
                    # Update existing website
                    existing_website.website_url = website_url
                    existing_website.update_time = stream_details.get('updateTime')
                    existing_website.save()
                    updated = True
                    logger.info(f"Updated website: {website_url}")
                else:
                    logger.info(f"Skipping existing website: {website_url}")
            else:
                # Create new website
                new_website = Website(
                    database=self.database,
                    website_id=stream_id,
                    property_db_id=property_db_id,
                    website_url=website_url,
                    create_time=stream_details.get('createTime'),
                    update_time=stream_details.get('updateTime')
                )
                new_website.save()
                created = True
                logger.info(f"Created website: {website_url}")
                
        except Exception as e:
            logger.error(f"Error syncing website {stream_id}: {str(e)}", exc_info=True)
            raise
        
        return created, updated
    
    def get_sync_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current sync status.
        
        Returns:
            Dictionary with counts of properties and websites in the database
        """
        try:
            properties_count = len(Property.find_all(self.database))
            websites_count = len(Website.find_all(self.database))
            
            # Get properties with their website counts
            properties_with_sites = []
            properties = Property.find_all(self.database, order_by="property_name ASC")
            
            for prop in properties:
                websites = prop.get_websites()
                properties_with_sites.append({
                    'property_id': prop.property_id,
                    'property_name': prop.property_name,
                    'account_id': prop.account_id,
                    'website_count': len(websites),
                    'websites': [{'url': w.website_url, 'id': w.website_id} for w in websites]
                })
            
            return {
                'total_properties': properties_count,
                'total_websites': websites_count,
                'properties': properties_with_sites
            }
            
        except Exception as e:
            logger.error(f"Error getting sync summary: {str(e)}", exc_info=True)
            return {
                'error': str(e),
                'total_properties': 0,
                'total_websites': 0,
                'properties': []
            }