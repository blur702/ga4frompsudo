#!/usr/bin/env python
"""
Check available permissions for the service account.
This script tests access to various Google APIs to see what the service account can access.
"""

import os
import json
import logging
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Path to the credentials file
CREDENTIALS_PATH = "credentials/ga4_credentials.json"

def check_api_access(api_name, api_version, resource_name, method_name, **method_args):
    """
    Generic function to test if the service account has access to a specific Google API.
    Returns a tuple of (success, response)
    """
    try:
        # Initialize credentials with appropriate scopes for the API
        scopes = []
        
        # Add appropriate scopes based on API
        if api_name == 'analyticsadmin' or api_name == 'analyticsdata':
            scopes = ['https://www.googleapis.com/auth/analytics.readonly']
        elif api_name == 'drive':
            scopes = ['https://www.googleapis.com/auth/drive.readonly']
        elif api_name == 'sheets':
            scopes = ['https://www.googleapis.com/auth/spreadsheets.readonly']
        elif api_name == 'calendar':
            scopes = ['https://www.googleapis.com/auth/calendar.readonly']
        
        credentials = Credentials.from_service_account_file(
            CREDENTIALS_PATH, scopes=scopes
        )
        
        # Initialize API service
        service = build(api_name, api_version, credentials=credentials)
        
        # Get the resource object
        resource = getattr(service, resource_name)()
        
        # Call the method
        method = getattr(resource, method_name)
        response = method(**method_args).execute()
        
        return True, response
    
    except HttpError as e:
        # Check if this is a permissions error
        if e.resp.status == 403:
            return False, f"Permission denied: {e.reason}"
        if e.resp.status == 404:
            return False, f"Not found: {e.reason}"
        return False, f"API error ({e.resp.status}): {e.reason}"
    except Exception as e:
        return False, f"Error: {str(e)}"

def main():
    """Test access to various Google APIs"""
    if not os.path.exists(CREDENTIALS_PATH):
        logger.error(f"Credentials file not found at {CREDENTIALS_PATH}")
        return
    
    # Get service account email
    with open(CREDENTIALS_PATH) as f:
        creds_data = json.load(f)
        email = creds_data.get('client_email')
        project_id = creds_data.get('project_id')
    
    print("\n" + "="*80)
    print("SERVICE ACCOUNT PERMISSION CHECK".center(80))
    print("="*80)
    print(f"\nService Account: {email}")
    print(f"Project ID: {project_id}")
    print("\nTesting access to various Google APIs...\n")
    
    # List of APIs to check
    apis_to_check = [
        # GA4 Admin API
        {
            "name": "Google Analytics Admin API (GA4)",
            "api_name": "analyticsadmin",
            "api_version": "v1beta",
            "resource_name": "accountSummaries",
            "method_name": "list",
            "args": {}
        },
        # GA4 Data API
        {
            "name": "Google Analytics Data API (GA4)",
            "api_name": "analyticsdata",
            "api_version": "v1beta", 
            "resource_name": "properties",
            "method_name": "runReport",
            "args": {"property": "properties/12345678", "body": {"dateRanges": [{"startDate": "7daysAgo", "endDate": "today"}], "metrics": [{"name": "activeUsers"}]}}
        },
        # Google Drive API
        {
            "name": "Google Drive API",
            "api_name": "drive",
            "api_version": "v3",
            "resource_name": "files",
            "method_name": "list",
            "args": {"pageSize": 10}
        },
        # Google Sheets API
        {
            "name": "Google Sheets API",
            "api_name": "sheets",
            "api_version": "v4",
            "resource_name": "spreadsheets",
            "method_name": "get",
            "args": {"spreadsheetId": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms", "includeGridData": False}
        },
        # Google Calendar API
        {
            "name": "Google Calendar API",
            "api_name": "calendar",
            "api_version": "v3",
            "resource_name": "calendarList",
            "method_name": "list",
            "args": {}
        }
    ]
    
    results = []
    for api in apis_to_check:
        print(f"Testing access to {api['name']}...")
        success, response = check_api_access(
            api["api_name"], api["api_version"], api["resource_name"], api["method_name"], **api["args"]
        )
        
        if success:
            print(f"✅ SUCCESS: Has access to {api['name']}")
            if isinstance(response, dict) and len(response) > 0:
                # Show some basic info about the response
                print(f"   Response contains: {', '.join(response.keys())}")
                if 'items' in response and isinstance(response['items'], list):
                    print(f"   Found {len(response['items'])} items")
        else:
            print(f"❌ FAILED: No access to {api['name']}")
            print(f"   Error: {response}")
        
        results.append({
            "api_name": api["name"],
            "has_access": success,
            "details": response if success and not isinstance(response, dict) else str(type(response))
        })
        print()
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY".center(80))
    print("="*80 + "\n")
    
    access_count = sum(1 for r in results if r["has_access"])
    print(f"The service account has access to {access_count} out of {len(apis_to_check)} tested APIs.\n")
    
    if access_count == 0:
        print("No API access was detected. Possible issues:")
        print("1. The service account may be new and have no permissions assigned")
        print("2. The API may not be enabled in the Google Cloud project")
        print("3. The service account may have been revoked or disabled\n")
        
        print("To grant GA4 access, follow these steps:")
        print("1. Log in to Google Analytics Admin")
        print("2. Go to Admin > Account Access Management")
        print("3. Add your service account email as a user with appropriate permissions")
        print(f"4. Add this email: {email}")
        print("5. Wait a few minutes for permissions to propagate")
    else:
        print("The service account has access to the following APIs:")
        for r in results:
            if r["has_access"]:
                print(f"- {r['api_name']}")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    try:
        # Check if required Google libraries are installed
        import google.oauth2.service_account
        import googleapiclient.discovery
        main()
    except ImportError:
        print("Required Google libraries not installed.")
        print("Please install them with: pip install google-api-python-client google-auth")