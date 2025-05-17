#!/usr/bin/env python
"""
List all GA4 properties with their IDs, names, and associated websites
"""

import os
import json
import csv
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Constants
CREDENTIALS_PATH = "credentials/ga4_credentials.json"
ACCOUNT_ID = "169438601"  # House Learning Center account ID
OUTPUT_CSV = "ga4_properties_list.csv"
OUTPUT_JSON = "ga4_properties_list.json"

def main():
    """List all GA4 properties in the account"""
    print("\n=== GA4 Properties Listing ===\n")
    
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
    
    # Initialize Admin API
    try:
        print("\nInitializing Admin API...")
        analytics_admin = build('analyticsadmin', 'v1beta', credentials=credentials)
        print("✅ Admin API initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing Admin API: {str(e)}")
        return False
    
    # Get account info
    try:
        print(f"\nFetching account details for ID: {ACCOUNT_ID}...")
        account = analytics_admin.accounts().get(name=f"accounts/{ACCOUNT_ID}").execute()
        account_name = account.get('displayName', 'Unknown Account')
        print(f"Account: {account_name} (ID: {ACCOUNT_ID})")
    except Exception as e:
        print(f"Warning: Could not fetch account details: {str(e)}")
        account_name = "Unknown Account"
        
    # List properties directly using the properties() method
    all_properties = []
    page_token = None
    page_num = 1
    total_properties = 0
    
    print("\nFetching properties (this may take some time for accounts with many properties)...")
    
    try:
        while True:
            # Get page of properties
            request = analytics_admin.properties().list(
                filter=f"parent:accounts/{ACCOUNT_ID}",
                pageSize=200,
                pageToken=page_token
            )
            response = request.execute()
            properties = response.get('properties', [])
            
            # Process properties
            total_on_page = len(properties)
            total_properties += total_on_page
            print(f"Processing page {page_num}: {total_on_page} properties found")
            
            # Process each property
            for prop in properties:
                property_id = prop.get('name', '').split('/')[-1]
                property_name = prop.get('displayName', 'Unnamed Property')
                
                property_info = {
                    'property_id': property_id,
                    'property_name': property_name,
                    'account_id': ACCOUNT_ID,
                    'account_name': account_name,
                    'create_time': prop.get('createTime', ''),
                    'update_time': prop.get('updateTime', ''),
                    'websites': []
                }
                
                # Get data streams (websites) for this property
                try:
                    streams = analytics_admin.properties().dataStreams().list(
                        parent=f"properties/{property_id}"
                    ).execute()
                    
                    for stream in streams.get('dataStreams', []):
                        if stream.get('webStreamData'):
                            website_url = stream.get('webStreamData', {}).get('defaultUri', '')
                            if website_url:
                                property_info['websites'].append(website_url)
                except Exception as e:
                    print(f"  Warning: Could not fetch streams for property {property_id}: {str(e)}")
                
                # Add to list
                all_properties.append(property_info)
                
            # Check for next page
            page_token = response.get('nextPageToken')
            if not page_token:
                break
                
            page_num += 1
    except HttpError as e:
        print(f"❌ API error listing properties: {e.reason}")
        # Continue with what we've got
    except Exception as e:
        print(f"❌ Error listing properties: {str(e)}")
        # Continue with what we've got
    
    # Summarize results
    print(f"\n✅ Found {total_properties} properties in account {account_name}")
    
    # Save properties to CSV
    try:
        with open(OUTPUT_CSV, 'w', newline='') as csvfile:
            fieldnames = ['property_id', 'property_name', 'account_id', 'account_name', 'websites', 'create_time', 'update_time']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for prop in all_properties:
                # Convert websites list to string
                prop_csv = prop.copy()
                prop_csv['websites'] = ', '.join(prop['websites'])
                writer.writerow(prop_csv)
                
        print(f"✅ Properties exported to {OUTPUT_CSV}")
    except Exception as e:
        print(f"❌ Error exporting to CSV: {str(e)}")
    
    # Save properties to JSON
    try:
        with open(OUTPUT_JSON, 'w') as jsonfile:
            json.dump(all_properties, jsonfile, indent=2)
            
        print(f"✅ Properties exported to {OUTPUT_JSON}")
    except Exception as e:
        print(f"❌ Error exporting to JSON: {str(e)}")
    
    # Print summary of first few properties
    if all_properties:
        print("\nSample of properties:")
        print("-" * 80)
        print(f"{'ID':<12} | {'Name':<35} | {'Website'}")
        print("-" * 80)
        
        for prop in all_properties[:10]:  # Show first 10
            website = prop['websites'][0] if prop['websites'] else 'No website'
            print(f"{prop['property_id']:<12} | {prop['property_name'][:35]:<35} | {website}")
            
        if len(all_properties) > 10:
            print(f"... and {len(all_properties) - 10} more properties")
    
    return True

if __name__ == "__main__":
    main()