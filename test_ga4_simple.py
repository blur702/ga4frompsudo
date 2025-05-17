#!/usr/bin/env python
"""
Basic GA4 API test to verify access to analytics data
"""

import os
import json
import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Constants
CREDENTIALS_PATH = "credentials/ga4_credentials.json"
PROPERTY_ID = "371939401"  # From our ga4_properties.json

def main():
    """Run a simple GA4 API test"""
    print("\n=== GA4 API Basic Test ===\n")
    
    # Check if credentials exist
    if not os.path.exists(CREDENTIALS_PATH):
        print(f"Error: Credentials file not found at {CREDENTIALS_PATH}")
        return False
        
    # Initialize credentials
    try:
        print("Initializing credentials...")
        credentials = Credentials.from_service_account_file(
            CREDENTIALS_PATH, 
            scopes=['https://www.googleapis.com/auth/analytics.readonly']
        )
        print("✅ Credentials initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing credentials: {str(e)}")
        return False
    
    # Check credentials info
    try:
        with open(CREDENTIALS_PATH) as f:
            creds_data = json.load(f)
            print(f"Service Account: {creds_data.get('client_email')}")
    except Exception as e:
        print(f"Warning: Could not read credentials info: {str(e)}")
    
    # Initialize Admin API for account/property info
    try:
        print("\nInitializing Admin API...")
        analytics_admin = build('analyticsadmin', 'v1beta', credentials=credentials)
        print("✅ Admin API initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing Admin API: {str(e)}")
        return False
    
    # Initialize Data API for reporting
    try:
        print("\nInitializing Data API...")
        analytics_data = build('analyticsdata', 'v1beta', credentials=credentials)
        print("✅ Data API initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing Data API: {str(e)}")
        return False
    
    # Test account access
    try:
        print("\nTesting account access...")
        account_summaries = analytics_admin.accountSummaries().list().execute()
        accounts = account_summaries.get('accountSummaries', [])
        
        if not accounts:
            print("❌ No accounts found or accessible!")
            return False
            
        print(f"✅ Found {len(accounts)} account(s):")
        for account in accounts:
            account_id = account['account'].split('/')[-1]
            account_name = account.get('displayName', 'Unnamed')
            print(f"- {account_name} (ID: {account_id})")
            
            # Check properties
            properties = account.get('propertySummaries', [])
            if properties:
                for prop in properties:
                    property_id = prop['property'].split('/')[-1]
                    property_name = prop.get('displayName', 'Unnamed')
                    print(f"  - Property: {property_name} (ID: {property_id})")
            else:
                print("  (No properties found)")
    except HttpError as e:
        print(f"❌ API error listing accounts: {e.reason}")
        return False
    except Exception as e:
        print(f"❌ Error listing accounts: {str(e)}")
        return False
    
    # Test running a simple report
    try:
        print(f"\nTesting report for property {PROPERTY_ID}...")
        
        # Get today and 30 days ago
        end_date = datetime.datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime('%Y-%m-%d')
        
        # Run report
        report = analytics_data.properties().runReport(
            property=f"properties/{PROPERTY_ID}",
            body={
                "dateRanges": [{"startDate": start_date, "endDate": end_date}],
                "dimensions": [{"name": "date"}],
                "metrics": [
                    {"name": "sessions"},
                    {"name": "totalUsers"},
                    {"name": "screenPageViews"}
                ]
            }
        ).execute()
        
        # Process report
        rows = report.get('rows', [])
        if rows:
            print(f"✅ Report returned {len(rows)} row(s) of data")
            
            # Show dimension headers
            dim_headers = [h.get('name') for h in report.get('dimensionHeaders', [])]
            metric_headers = [h.get('name') for h in report.get('metricHeaders', [])]
            
            # Print headers
            print("\nData sample:")
            print(f"{', '.join(dim_headers)} | {', '.join(metric_headers)}")
            print("-" * 60)
            
            # Print a few rows
            for i, row in enumerate(rows[:5]):
                dims = [v.get('value') for v in row.get('dimensionValues', [])]
                metrics = [v.get('value') for v in row.get('metricValues', [])]
                print(f"{', '.join(dims)} | {', '.join(metrics)}")
        else:
            print("✅ Report executed successfully, but returned no data")
            print("This is normal for new properties or if no activity in date range")
        
        print("\n✅ API access test completed successfully")
        return True
    except HttpError as e:
        print(f"❌ API error running report: {e.reason}")
        return False
    except Exception as e:
        print(f"❌ Error running report: {str(e)}")
        return False

if __name__ == "__main__":
    main()