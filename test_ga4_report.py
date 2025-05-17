#!/usr/bin/env python
"""
GA4 Report Data Test - Verify that we can access report data from GA4
"""

import os
import json
import logging
import datetime
from pprint import pprint
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
PROPERTY_ID = "371939401"  # From our ga4_properties.json

def test_basic_report():
    """Test that we can run a basic GA4 report"""
    try:
        # Initialize credentials
        scopes = ['https://www.googleapis.com/auth/analytics.readonly']
        credentials = Credentials.from_service_account_file(
            CREDENTIALS_PATH, scopes=scopes
        )
        
        # Initialize analytics data API
        analytics_data = build('analyticsdata', 'v1beta', credentials=credentials)
        
        # Calculate date range
        end_date = datetime.datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime('%Y-%m-%d')
        
        print(f"\nRunning report for property {PROPERTY_ID}")
        print(f"Date range: {start_date} to {end_date}")
        
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
                ],
                "limit": 10
            }
        ).execute()
        
        print("\nReport results:")
        print("==============")
        
        # Print dimension headers
        dimension_headers = [header.get('name') for header in report.get('dimensionHeaders', [])]
        metric_headers = [header.get('name') for header in report.get('metricHeaders', [])]
        
        # Print header row
        print(f"{', '.join(dimension_headers)} | {', '.join(metric_headers)}")
        print("-" * 60)
        
        # Print rows
        rows = report.get('rows', [])
        if not rows:
            print("No data in report")
        else:
            for row in rows:
                dimensions = [value.get('value') for value in row.get('dimensionValues', [])]
                metrics = [value.get('value') for value in row.get('metricValues', [])]
                print(f"{', '.join(dimensions)} | {', '.join(metrics)}")
        
        return True
    except HttpError as e:
        logger.error(f"API error: {e.reason}")
        print(f"\nError accessing GA4 API: {e.reason}")
        if hasattr(e, 'resp') and e.resp.status == 403:
            print("\nPermission denied. The service account may not have sufficient access.")
            print("Check that the service account has been granted at least 'Viewer' role in GA4.")
        return False
    except Exception as e:
        logger.error(f"Error running report: {str(e)}")
        print(f"\nError running report: {str(e)}")
        return False

def test_traffic_sources():
    """Test retrieving traffic sources data"""
    try:
        # Initialize credentials
        scopes = ['https://www.googleapis.com/auth/analytics.readonly']
        credentials = Credentials.from_service_account_file(
            CREDENTIALS_PATH, scopes=scopes
        )
        
        # Initialize analytics data API
        analytics_data = build('analyticsdata', 'v1beta', credentials=credentials)
        
        # Calculate date range
        end_date = datetime.datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime('%Y-%m-%d')
        
        print(f"\nRunning traffic sources report for property {PROPERTY_ID}")
        print(f"Date range: {start_date} to {end_date}")
        
        # Run report
        report = analytics_data.properties().runReport(
            property=f"properties/{PROPERTY_ID}",
            body={
                "dateRanges": [{"startDate": start_date, "endDate": end_date}],
                "dimensions": [{"name": "sessionSource"}],
                "metrics": [
                    {"name": "sessions"},
                    {"name": "totalUsers"}
                ],
                "orderBys": [
                    {"metric": {"metricName": "sessions"}, "desc": True}
                ],
                "limit": 10
            }
        ).execute()
        
        print("\nTraffic Sources:")
        print("===============")
        
        # Print dimension headers
        dimension_headers = [header.get('name') for header in report.get('dimensionHeaders', [])]
        metric_headers = [header.get('name') for header in report.get('metricHeaders', [])]
        
        # Print header row
        print(f"{', '.join(dimension_headers)} | {', '.join(metric_headers)}")
        print("-" * 60)
        
        # Print rows
        rows = report.get('rows', [])
        if not rows:
            print("No data in report")
        else:
            for row in rows:
                dimensions = [value.get('value') for value in row.get('dimensionValues', [])]
                metrics = [value.get('value') for value in row.get('metricValues', [])]
                print(f"{', '.join(dimensions)} | {', '.join(metrics)}")
        
        return True
    except Exception as e:
        logger.error(f"Error running traffic sources report: {str(e)}")
        print(f"\nError running traffic sources report: {str(e)}")
        return False

if __name__ == "__main__":
    print("\n" + "="*80)
    print("GA4 REPORT DATA TEST".center(80))
    print("="*80)
    
    # Check if the credentials file exists
    if not os.path.exists(CREDENTIALS_PATH):
        print(f"\nCredentials file not found at {CREDENTIALS_PATH}")
        print("Please add the GA4 service account credentials file first.")
        exit(1)
    
    # Run basic report test
    if test_basic_report():
        print("\n✅ Basic report test successful!")
    else:
        print("\n❌ Basic report test failed!")
    
    # Run traffic sources test
    if test_traffic_sources():
        print("\n✅ Traffic sources report test successful!")
    else:
        print("\n❌ Traffic sources report test failed!")
    
    print("\n" + "="*80)