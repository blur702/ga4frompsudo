#!/usr/bin/env python
"""
Check all GA4 permissions and objects the service account can access
"""

import os
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Constants
CREDENTIALS_PATH = "credentials/ga4_credentials.json"

def main():
    """Check all GA4 permissions"""
    print("\n=== GA4 Permissions Check ===\n")
    
    # Initialize credentials
    try:
        print("Initializing credentials...")
        credentials = Credentials.from_service_account_file(
            CREDENTIALS_PATH, 
            scopes=['https://www.googleapis.com/auth/analytics.readonly']
        )
        print("✅ Credentials initialized successfully")
        
        # Get service account email
        with open(CREDENTIALS_PATH) as f:
            creds_data = json.load(f)
            service_account_email = creds_data.get('client_email', 'Unknown')
            print(f"Service Account: {service_account_email}")
    except Exception as e:
        print(f"❌ Error initializing credentials: {str(e)}")
        return False
    
    # Initialize Admin API
    try:
        print("\nInitializing Admin API...")
        analytics_admin = build('analyticsadmin', 'v1beta', credentials=credentials)
        print("✅ Admin API initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing Admin API: {str(e)}")
        return False
    
    # Initialize Data API
    try:
        print("\nInitializing Data API...")
        analytics_data = build('analyticsdata', 'v1beta', credentials=credentials)
        print("✅ Data API initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing Data API: {str(e)}")
        return False
    
    # List account summaries (fastest way to see what we have access to)
    try:
        print("\nListing account summaries...")
        accounts_response = analytics_admin.accountSummaries().list().execute()
        accounts = accounts_response.get('accountSummaries', [])
        
        if not accounts:
            print("❌ No accounts found in summaries!")
        else:
            print(f"✅ Found {len(accounts)} account(s) in summaries")
            
            for account in accounts:
                account_id = account['account'].split('/')[-1]
                account_name = account.get('displayName', 'Unnamed Account')
                properties = account.get('propertySummaries', [])
                
                print(f"\nAccount: {account_name} (ID: {account_id})")
                print(f"Properties in summary: {len(properties)}")
                
                # Print first few properties
                for i, prop in enumerate(properties[:5]):
                    property_id = prop['property'].split('/')[-1]
                    property_name = prop.get('displayName', 'Unnamed Property')
                    print(f"  - {property_name} (ID: {property_id})")
                
                if len(properties) > 5:
                    print(f"  ... and {len(properties) - 5} more properties")
    except HttpError as e:
        print(f"❌ API error listing account summaries: {e.reason}")
    except Exception as e:
        print(f"❌ Error listing account summaries: {str(e)}")
    
    # Try to list accounts directly
    try:
        print("\nListing accounts directly...")
        accounts_response = analytics_admin.accounts().list().execute()
        accounts = accounts_response.get('accounts', [])
        
        if not accounts:
            print("❌ No accounts found with direct listing!")
        else:
            print(f"✅ Found {len(accounts)} account(s) with direct listing")
            
            for account in accounts:
                account_id = account['name'].split('/')[-1]
                account_name = account.get('displayName', 'Unnamed Account')
                print(f"  - {account_name} (ID: {account_id})")
    except HttpError as e:
        print(f"❌ API error listing accounts directly: {e.reason}")
        print(f"   This might be due to permission restrictions")
    except Exception as e:
        print(f"❌ Error listing accounts directly: {str(e)}")
    
    # Get all accessible resources - try each account ID from summaries
    for account in accounts:
        if 'account' in account:
            account_id = account['account'].split('/')[-1]
        else:
            account_id = account['name'].split('/')[-1]
        account_name = account.get('displayName', 'Unnamed Account')
        
        print(f"\nChecking accessible resources in account: {account_name} (ID: {account_id})...")
        
        # Check if we can access the account directly
        try:
            print(f"Attempting to access account directly...")
            account_details = analytics_admin.accounts().get(name=f"accounts/{account_id}").execute()
            print(f"✅ Can access account directly: {account_details.get('displayName', 'Unnamed')}")
        except HttpError as e:
            print(f"❌ Cannot access account directly: {e.reason}")
        except Exception as e:
            print(f"❌ Error accessing account: {str(e)}")
        
        # Try to list properties directly
        try:
            print(f"Listing properties directly...")
            properties_response = analytics_admin.properties().list(
                filter=f"parent:accounts/{account_id}"
            ).execute()
            properties = properties_response.get('properties', [])
            
            if not properties:
                print(f"❌ No properties found with direct listing!")
            else:
                print(f"✅ Found {len(properties)} propert(ies) with direct listing")
                
                for i, prop in enumerate(properties[:5]):
                    property_id = prop['name'].split('/')[-1]
                    property_name = prop.get('displayName', 'Unnamed Property')
                    print(f"  - {property_name} (ID: {property_id})")
                
                if len(properties) > 5:
                    print(f"  ... and {len(properties) - 5} more properties")
        except HttpError as e:
            print(f"❌ API error listing properties directly: {e.reason}")
        except Exception as e:
            print(f"❌ Error listing properties directly: {str(e)}")
        
        # Try listing all accessible objects
        print(f"\nTesting access to various Google Analytics objects...\n")
        
        # Test account-level access
        try:
            user_links = analytics_admin.accounts().userLinks().list(
                parent=f"accounts/{account_id}"
            ).execute()
            print(f"✅ Can access account user links")
            print(f"   Found {len(user_links.get('userLinks', []))} user links")
        except HttpError as e:
            print(f"❌ Cannot access account user links: {e.reason}")
        except Exception as e:
            print(f"❌ Error accessing account user links: {str(e)}")
        
        # Get properties from the account summary
        properties = account.get('propertySummaries', [])
        
        # Test property-level access for the first few properties
        for i, prop in enumerate(properties[:3]):
            property_id = prop['property'].split('/')[-1]
            property_name = prop.get('displayName', 'Unnamed Property')
            
            print(f"\nChecking access for property: {property_name} (ID: {property_id})...")
            
            # Try to get the property directly
            try:
                property_details = analytics_admin.properties().get(
                    name=f"properties/{property_id}"
                ).execute()
                print(f"✅ Can access property details")
            except HttpError as e:
                print(f"❌ Cannot access property details: {e.reason}")
            except Exception as e:
                print(f"❌ Error accessing property details: {str(e)}")
            
            # Try to list data streams
            try:
                streams = analytics_admin.properties().dataStreams().list(
                    parent=f"properties/{property_id}"
                ).execute()
                
                print(f"✅ Can access data streams")
                print(f"   Found {len(streams.get('dataStreams', []))} data stream(s)")
                
                # List data streams
                for stream in streams.get('dataStreams', []):
                    stream_id = stream['name'].split('/')[-1]
                    stream_type = next((k for k in stream if k.endswith('StreamData')), None)
                    
                    if stream_type == 'webStreamData':
                        website = stream.get('webStreamData', {}).get('defaultUri', 'Unknown')
                        print(f"   - Web Stream: {website} (ID: {stream_id})")
                    else:
                        stream_name = stream.get('displayName', 'Unnamed Stream')
                        print(f"   - Stream: {stream_name} (ID: {stream_id}, Type: {stream_type})")
            except HttpError as e:
                print(f"❌ Cannot access data streams: {e.reason}")
            except Exception as e:
                print(f"❌ Error accessing data streams: {str(e)}")
            
            # Try to access other property-level features
            try:
                user_links = analytics_admin.properties().userLinks().list(
                    parent=f"properties/{property_id}"
                ).execute()
                print(f"✅ Can access property user links")
                print(f"   Found {len(user_links.get('userLinks', []))} user links")
            except HttpError as e:
                print(f"❌ Cannot access property user links: {e.reason}")
            except Exception as e:
                print(f"❌ Error accessing property user links: {str(e)}")
            
            # Try to run a simple report
            try:
                report = analytics_data.properties().runReport(
                    property=f"properties/{property_id}",
                    body={
                        "dateRanges": [
                            {"startDate": "30daysAgo", "endDate": "today"}
                        ],
                        "metrics": [{"name": "activeUsers"}]
                    }
                ).execute()
                
                print(f"✅ Can run reports")
                
                # Check if there's data
                has_data = 'rows' in report and len(report['rows']) > 0
                if has_data:
                    users = report['rows'][0]['metricValues'][0]['value']
                    print(f"   Active users in last 30 days: {users}")
                else:
                    print(f"   No data found in report")
            except HttpError as e:
                print(f"❌ Cannot run reports: {e.reason}")
            except Exception as e:
                print(f"❌ Error running report: {str(e)}")
            
            print("-" * 50)
        
        if len(properties) > 3:
            print(f"Skipping checks for {len(properties) - 3} other properties...")
    
    print("\n=== Permissions Check Complete ===")
    
    # Provide guidance on expanding access
    print("\nGUIDANCE FOR EXPANDING ACCESS:")
    print("1. If you need to see more accounts/properties:")
    print(f"   - Add {service_account_email} to additional GA4 accounts")
    print("   - Grant at least 'Viewer' role for each account")
    print("2. If you have permission issues:")
    print("   - Check your role in each account (need at least 'Viewer')")
    print("   - For property-level access, make sure you're added at the property level")
    print("3. For data access issues:")
    print("   - Verify the property has data collection set up correctly")
    print("   - Check date ranges in report requests")
    
    return True

if __name__ == "__main__":
    main()