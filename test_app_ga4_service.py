#!/usr/bin/env python
"""
Test the app's GA4 service in the application context.
"""

import os
import sys
import logging
from flask import Flask
from pprint import pprint

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create a simple Flask app context
app = Flask(__name__)
app.config['GA4_CREDENTIALS_PATH'] = os.path.abspath('credentials/ga4_credentials.json')

# Import after app is created to avoid circular imports
from app.services.ga4_service import GA4Service

def test_ga4_service():
    """Test the GA4Service in the app context"""
    with app.app_context():
        print("\n" + "="*80)
        print("TESTING GA4 SERVICE".center(80))
        print("="*80 + "\n")
        
        # Initialize the service
        ga4_service = GA4Service()
        
        # Check if service is available
        if not ga4_service.is_available():
            print("❌ GA4 Service is not available!")
            return False
            
        print("✅ GA4 Service is available\n")
        
        # List accounts
        try:
            accounts = ga4_service.list_account_summaries()
            print(f"Found {len(accounts)} GA4 account(s):")
            
            if not accounts:
                print("❌ No GA4 accounts found or accessible!")
                return False
                
            for account in accounts:
                account_id = account.get('name', '').split('/')[-1]
                account_name = account.get('displayName', 'Unnamed Account')
                print(f"- Account: {account_name} (ID: {account_id})")
                
                # Check properties
                properties = account.get('propertySummaries', [])
                if not properties:
                    print("  ❌ No properties found in this account!")
                    continue
                    
                # List properties
                for prop in properties:
                    property_id = prop.get('property', '').split('/')[-1]
                    property_name = prop.get('displayName', 'Unnamed Property')
                    print(f"  - Property: {property_name} (ID: {property_id})")
                    
                    # Try to get a report
                    try:
                        print(f"\nTesting report for property {property_id}...")
                        report = ga4_service.get_traffic_report(
                            property_id,
                            date_range="last30days"
                        )
                        
                        if report and 'rows' in report:
                            print(f"✅ Successfully ran report!")
                            print(f"Report contains {len(report.get('rows', []))} row(s)")
                            
                            # Print first few rows if available
                            rows = report.get('rows', [])
                            if rows:
                                print("\nSample data:")
                                # Get headers
                                dim_headers = [h.get('name') for h in report.get('dimensionHeaders', [])]
                                metric_headers = [h.get('name') for h in report.get('metricHeaders', [])]
                                headers = dim_headers + metric_headers
                                
                                # Print header row
                                print(" | ".join(headers))
                                print("-" * 50)
                                
                                # Print a few rows
                                for i, row in enumerate(rows[:5]):
                                    dim_values = [v.get('value') for v in row.get('dimensionValues', [])]
                                    metric_values = [v.get('value') for v in row.get('metricValues', [])]
                                    values = dim_values + metric_values
                                    print(" | ".join(values))
                        else:
                            print("❌ Report contains no data!")
                    except Exception as e:
                        print(f"❌ Error running report: {str(e)}")
                        
            print("\n" + "="*80)
            return True
        except Exception as e:
            print(f"❌ Error testing GA4 service: {str(e)}")
            return False

if __name__ == "__main__":
    test_ga4_service()