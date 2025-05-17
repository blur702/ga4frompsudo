#!/usr/bin/env python
"""
GA4 Helper Script - Helps with setting up GA4 permissions and accessing GA4 data.

This script provides utility functions to:
1. Check credentials and permissions
2. List GA4 accounts and properties
3. Extract property IDs, names, and website information
4. Output in a structured format for integration with the dashboard
"""

import os
import json
import logging
import datetime
from typing import Dict, List, Any, Optional

try:
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GA4_LIBRARIES_AVAILABLE = True
except ImportError:
    GA4_LIBRARIES_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Path to the credentials file
CREDENTIALS_PATH = "credentials/ga4_credentials.json"

class GA4Helper:
    """Helper class for GA4 operations"""
    
    def __init__(self, credentials_path: str = CREDENTIALS_PATH):
        """Initialize the GA4 Helper"""
        self.credentials_path = credentials_path
        self.scopes = ['https://www.googleapis.com/auth/analytics.readonly']
        self._analytics_admin = None
        self._analytics_data = None
        
        # Check if GA4 libraries are available
        if not GA4_LIBRARIES_AVAILABLE:
            logger.error("Google libraries not installed. Run: pip install google-api-python-client google-auth")
            return
            
        # Check if credentials file exists
        if not os.path.exists(self.credentials_path):
            logger.error(f"Credentials file not found at {self.credentials_path}")
            return
            
        # Initialize services
        try:
            # Load service account credentials
            credentials = Credentials.from_service_account_file(
                self.credentials_path, scopes=self.scopes
            )
            
            # Initialize analytics admin API (for account and property info)
            self._analytics_admin = build('analyticsadmin', 'v1beta', credentials=credentials)
            
            # Initialize analytics data API (for report data)
            self._analytics_data = build('analyticsdata', 'v1beta', credentials=credentials)
            
            logger.info("GA4 services initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize GA4 services: {str(e)}")
    
    def is_available(self) -> bool:
        """Check if GA4 services are available"""
        return self._analytics_admin is not None and self._analytics_data is not None
    
    def get_service_account_email(self) -> Optional[str]:
        """Get the service account email from credentials file"""
        try:
            with open(self.credentials_path) as f:
                creds_data = json.load(f)
                return creds_data.get('client_email')
        except Exception as e:
            logger.error(f"Error reading credentials file: {str(e)}")
            return None
    
    def list_accounts(self) -> List[Dict[str, Any]]:
        """List available GA4 accounts"""
        if not self.is_available():
            logger.error("GA4 services not available")
            return []
            
        try:
            response = self._analytics_admin.accountSummaries().list().execute()
            accounts = response.get('accountSummaries', [])
            logger.info(f"Found {len(accounts)} GA4 account(s)")
            return accounts
        except HttpError as e:
            logger.error(f"API error: {e.reason}")
            return []
        except Exception as e:
            logger.error(f"Error listing accounts: {str(e)}")
            return []
    
    def list_properties(self, account_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List properties, optionally filtered by account ID.
        
        Args:
            account_id: Optional GA4 account ID to filter properties
            
        Returns:
            List of property dictionaries
        """
        if not self.is_available():
            logger.error("GA4 services not available")
            return []
            
        try:
            accounts = self.list_accounts()
            properties = []
            
            for account in accounts:
                # Skip if account_id is specified and doesn't match
                if account_id and account['account'].split('/')[-1] != account_id:
                    continue
                    
                account_name = account.get('displayName', 'Unnamed Account')
                account_id = account['account'].split('/')[-1]
                
                # Get properties from account summary
                for prop in account.get('propertySummaries', []):
                    property_id = prop['property'].split('/')[-1]
                    property_name = prop.get('displayName', 'Unnamed Property')
                    
                    # Get property details
                    property_details = {
                        'account_id': account_id,
                        'account_name': account_name,
                        'property_id': property_id,
                        'property_name': property_name,
                        'create_time': prop.get('createTime', ''),
                        'websites': []
                    }
                    
                    # Try to get website information
                    try:
                        streams = self._analytics_admin.properties().dataStreams().list(
                            parent=f"properties/{property_id}"
                        ).execute()
                        
                        for stream in streams.get('dataStreams', []):
                            if stream.get('webStreamData'):
                                website_url = stream.get('webStreamData', {}).get('defaultUri', '')
                                if website_url:
                                    property_details['websites'].append(website_url)
                    except Exception as e:
                        logger.warning(f"Could not fetch website info for property {property_id}: {str(e)}")
                    
                    properties.append(property_details)
            
            return properties
        except Exception as e:
            logger.error(f"Error listing properties: {str(e)}")
            return []
    
    def get_real_time_users(self, property_id: str) -> int:
        """
        Get real-time active users for a GA4 property.
        
        Args:
            property_id: GA4 property ID
            
        Returns:
            Number of active users
        """
        if not self.is_available():
            logger.error("GA4 services not available")
            return 0
            
        try:
            report = self._analytics_data.properties().runRealtimeReport(
                property=f"properties/{property_id}",
                body={
                    "metrics": [{"name": "activeUsers"}]
                }
            ).execute()
            
            if 'rows' in report and len(report['rows']) > 0:
                return int(report['rows'][0]['metricValues'][0]['value'])
            return 0
        except Exception as e:
            logger.error(f"Error getting real-time users: {str(e)}")
            return 0
    
    def get_traffic_metrics(self, property_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Get basic traffic metrics for a GA4 property.
        
        Args:
            property_id: GA4 property ID
            days: Number of days of data to retrieve
            
        Returns:
            Dictionary with traffic metrics
        """
        if not self.is_available():
            logger.error("GA4 services not available")
            return {}
            
        try:
            # Calculate date range
            end_date = datetime.datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime('%Y-%m-%d')
            
            # Run report
            report = self._analytics_data.properties().runReport(
                property=f"properties/{property_id}",
                body={
                    "dateRanges": [{"startDate": start_date, "endDate": end_date}],
                    "metrics": [
                        {"name": "sessions"},
                        {"name": "totalUsers"},
                        {"name": "newUsers"},
                        {"name": "screenPageViews"},
                        {"name": "averageSessionDuration"}
                    ]
                }
            ).execute()
            
            # Process results
            metrics = {}
            if 'rows' in report and len(report['rows']) > 0:
                for i, header in enumerate(report.get('metricHeaders', [])):
                    metric_name = header.get('name', f'metric_{i}')
                    metric_value = report['rows'][0]['metricValues'][i]['value']
                    metrics[metric_name] = metric_value
            
            return metrics
        except Exception as e:
            logger.error(f"Error getting traffic metrics: {str(e)}")
            return {}

def print_setup_instructions(email: str):
    """Print GA4 setup instructions"""
    print("\n" + "="*80)
    print("GA4 SETUP INSTRUCTIONS".center(80))
    print("="*80 + "\n")
    
    print(f"Service Account Email: {email}\n")
    print("To grant GA4 access, follow these steps:\n")
    print("1. Log in to Google Analytics (https://analytics.google.com/)")
    print("2. Click the Admin gear icon in the bottom left")
    print("3. In the Account column, select the account you want to give access to")
    print("4. Click 'Account Access Management'")
    print("5. Click the blue '+' button")
    print(f"6. Enter the service account email: {email}")
    print("7. Select 'Viewer' role (minimum required)")
    print("8. Click 'Add'")
    print("\nIf you need property-level access:\n")
    print("1. Still in Admin, select the specific property in the Property column")
    print("2. Click 'Property Access Management'")
    print("3. Click the blue '+' button")
    print(f"4. Enter the same service account email: {email}")
    print("5. Select 'Viewer' role (minimum required)")
    print("6. Click 'Add'\n")
    
    print("After adding permissions, wait a few minutes for them to propagate.")
    print("Then run this script again to verify access.")
    print("\n" + "="*80)

def check_permissions_and_print_results():
    """Check GA4 permissions and print results"""
    # Create helper
    helper = GA4Helper()
    
    if not helper.is_available():
        print("\nGA4 services not available. Check that required libraries are installed.")
        return
    
    # Get service account email
    email = helper.get_service_account_email()
    if not email:
        print("\nCould not determine service account email from credentials file.")
        return
    
    # List accounts
    accounts = helper.list_accounts()
    
    print("\n" + "="*80)
    print("GA4 PERMISSIONS CHECK".center(80))
    print("="*80 + "\n")
    
    print(f"Service Account Email: {email}")
    
    if not accounts:
        print("\nNo GA4 accounts accessible. The service account needs permissions.")
        print_setup_instructions(email)
        return
    
    print(f"\nFound {len(accounts)} accessible GA4 account(s):")
    for account in accounts:
        account_id = account['account'].split('/')[-1]
        account_name = account.get('displayName', 'Unnamed Account')
        property_count = len(account.get('propertySummaries', []))
        
        print(f"\n- Account: {account_name} (ID: {account_id})")
        print(f"  Properties: {property_count}")
        
        # List properties for this account
        if property_count > 0:
            for prop in account.get('propertySummaries', []):
                property_id = prop['property'].split('/')[-1]
                property_name = prop.get('displayName', 'Unnamed Property')
                
                print(f"  - Property: {property_name} (ID: {property_id})")
                
                # Try to get website info and real-time users
                try:
                    # Get websites
                    properties = helper.list_properties(account_id)
                    for p in properties:
                        if p['property_id'] == property_id:
                            websites = p.get('websites', [])
                            if websites:
                                print(f"    Websites: {', '.join(websites)}")
                            
                            # Get real-time users
                            active_users = helper.get_real_time_users(property_id)
                            print(f"    Active Users (now): {active_users}")
                            
                            # Get basic metrics
                            metrics = helper.get_traffic_metrics(property_id, 7)
                            if metrics:
                                print(f"    Last 7 days:")
                                print(f"      Sessions: {metrics.get('sessions', 'N/A')}")
                                print(f"      Users: {metrics.get('totalUsers', 'N/A')}")
                                print(f"      New Users: {metrics.get('newUsers', 'N/A')}")
                                print(f"      Page Views: {metrics.get('screenPageViews', 'N/A')}")
                except Exception as e:
                    print(f"    Error getting details: {str(e)}")
        
    print("\n" + "="*80)
    
    # Save property info to file
    properties = helper.list_properties()
    if properties:
        with open('ga4_properties.json', 'w') as f:
            json.dump(properties, f, indent=2)
        print(f"\nProperty information saved to ga4_properties.json")
        print("You can use this file with the GA4 Analytics Dashboard")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    # Check if required libraries are available
    if not GA4_LIBRARIES_AVAILABLE:
        print("Required Google libraries not installed.")
        print("Please install them with: pip install google-api-python-client google-auth")
        exit(1)
    
    check_permissions_and_print_results()