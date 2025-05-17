#!/usr/bin/env python
"""
List all GA4 accounts and properties the service account has access to
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
OUTPUT_CSV = "all_ga4_properties.csv"
OUTPUT_JSON = "all_ga4_properties.json"

def main():
    """List all GA4 accounts and properties the service account has access to"""
    print("\n=== GA4 Accounts and Properties Listing ===\n")
    
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
    
    # Load service account email from credentials
    try:
        with open(CREDENTIALS_PATH) as f:
            creds_data = json.load(f)
            service_account_email = creds_data.get('client_email', 'Unknown')
            print(f"Service Account: {service_account_email}")
    except Exception as e:
        print(f"Warning: Could not read service account email: {str(e)}")
        service_account_email = "Unknown"
    
    # Initialize Admin API
    try:
        print("\nInitializing Admin API...")
        analytics_admin = build('analyticsadmin', 'v1beta', credentials=credentials)
        print("✅ Admin API initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing Admin API: {str(e)}")
        return False
    
    # List all accounts the service account has access to
    try:
        print("\nListing all accessible GA4 accounts...")
        accounts_response = analytics_admin.accountSummaries().list().execute()
        accounts = accounts_response.get('accountSummaries', [])
        
        if not accounts:
            print("❌ No accounts found or accessible!")
            return False
            
        print(f"✅ Found {len(accounts)} accessible account(s)")
    except HttpError as e:
        print(f"❌ API error listing accounts: {e.reason}")
        return False
    except Exception as e:
        print(f"❌ Error listing accounts: {str(e)}")
        return False
    
    # Process each account and gather all properties
    all_properties = []
    total_properties = 0
    
    for account in accounts:
        account_id = account['account'].split('/')[-1]
        account_name = account.get('displayName', 'Unnamed Account')
        properties_in_summary = account.get('propertySummaries', [])
        
        print(f"\nAccount: {account_name} (ID: {account_id})")
        print(f"Found {len(properties_in_summary)} properties in account summary")
        
        # Try to list ALL properties in the account using properties().list() method
        try:
            print(f"Fetching complete property details for account {account_id}...")
            
            # Use pagination to get all properties
            page_token = None
            page_num = 1
            account_properties = []
            
            while True:
                # Get page of properties
                request = analytics_admin.properties().list(
                    filter=f"parent:accounts/{account_id}",
                    pageSize=200,
                    pageToken=page_token
                )
                response = request.execute()
                properties = response.get('properties', [])
                
                # Process properties
                total_on_page = len(properties)
                print(f"  Processing page {page_num}: {total_on_page} properties found")
                
                # Process each property
                for prop in properties:
                    property_id = prop.get('name', '').split('/')[-1]
                    property_name = prop.get('displayName', 'Unnamed Property')
                    
                    property_info = {
                        'property_id': property_id,
                        'property_name': property_name,
                        'account_id': account_id,
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
                        print(f"    Warning: Could not fetch streams for property {property_id}: {str(e)}")
                    
                    # Add to lists
                    account_properties.append(property_info)
                    all_properties.append(property_info)
                
                # Check for next page
                page_token = response.get('nextPageToken')
                if not page_token:
                    break
                    
                page_num += 1
            
            # Update count
            total_properties += len(account_properties)
            print(f"  ✅ Successfully fetched {len(account_properties)} property details")
            
            # If counts don't match, show warning
            if len(account_properties) != len(properties_in_summary):
                print(f"  ⚠️ Warning: Found {len(account_properties)} properties but account summary showed {len(properties_in_summary)}")
        
        except HttpError as e:
            print(f"  ❌ API error listing properties: {e.reason}")
            
            # Fall back to using properties from account summary
            print(f"  Falling back to properties from account summary...")
            
            for prop_summary in properties_in_summary:
                property_id = prop_summary['property'].split('/')[-1]
                property_name = prop_summary.get('displayName', 'Unnamed Property')
                
                property_info = {
                    'property_id': property_id,
                    'property_name': property_name,
                    'account_id': account_id,
                    'account_name': account_name,
                    'create_time': '',  # Not available in summary
                    'update_time': '',  # Not available in summary
                    'websites': []
                }
                
                # Try to get streams
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
                    print(f"    Warning: Could not fetch streams for property {property_id}: {str(e)}")
                
                # Add to lists
                all_properties.append(property_info)
            
            # Update count
            total_properties += len(properties_in_summary)
            print(f"  ✅ Successfully processed {len(properties_in_summary)} properties from account summary")
        
        except Exception as e:
            print(f"  ❌ Error processing account properties: {str(e)}")
            # Continue with next account
    
    # Summarize results
    print(f"\n=== SUMMARY ===")
    print(f"Total accounts: {len(accounts)}")
    print(f"Total properties: {total_properties}")
    
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
                
        print(f"\n✅ All properties exported to {OUTPUT_CSV}")
    except Exception as e:
        print(f"\n❌ Error exporting to CSV: {str(e)}")
    
    # Save properties to JSON
    try:
        with open(OUTPUT_JSON, 'w') as jsonfile:
            json.dump(all_properties, jsonfile, indent=2)
            
        print(f"✅ All properties exported to {OUTPUT_JSON}")
    except Exception as e:
        print(f"❌ Error exporting to JSON: {str(e)}")
    
    # Print sample properties
    if all_properties:
        print("\nSample of properties:")
        print("-" * 100)
        print(f"{'Property ID':<12} | {'Property Name':<35} | {'Account Name':<25} | {'Website'}")
        print("-" * 100)
        
        for prop in all_properties[:10]:  # Show first 10
            website = prop['websites'][0] if prop['websites'] else 'No website'
            print(f"{prop['property_id']:<12} | {prop['property_name'][:35]:<35} | {prop['account_name'][:25]:<25} | {website}")
            
        if len(all_properties) > 10:
            print(f"... and {len(all_properties) - 10} more properties")
    
    return True

if __name__ == "__main__":
    main()