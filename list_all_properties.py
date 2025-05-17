#!/usr/bin/env python
"""
List all GA4 properties accessible to the service account using searchGoogleAdsLinks
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
OUTPUT_CSV = "all_ga4_properties_search.csv"
OUTPUT_JSON = "all_ga4_properties_search.json"

def main():
    """List all GA4 properties using various methods"""
    print("\n=== Listing All GA4 Properties ===\n")
    
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
    
    # Get all available properties by checking various endpoints
    all_properties = []
    
    # Method 1: Get properties through account summaries
    try:
        print("\nMethod 1: Getting properties from account summaries...")
        response = analytics_admin.accountSummaries().list().execute()
        accounts = response.get('accountSummaries', [])
        
        if not accounts:
            print("❌ No accounts found in summaries")
        else:
            print(f"✅ Found {len(accounts)} account(s) in summaries")
            
            # Process each account
            for account in accounts:
                account_id = account['account'].split('/')[-1]
                account_name = account.get('displayName', 'Unnamed Account')
                
                print(f"\nAccount: {account_name} (ID: {account_id})")
                
                # Get properties from account summary
                properties = account.get('propertySummaries', [])
                print(f"Found {len(properties)} properties in account summary")
                
                for prop in properties:
                    property_id = prop['property'].split('/')[-1]
                    property_name = prop.get('displayName', 'Unnamed Property')
                    
                    # Add to our list
                    property_info = {
                        'property_id': property_id,
                        'property_name': property_name,
                        'account_id': account_id,
                        'account_name': account_name,
                        'websites': [],
                        'source': 'account_summary'
                    }
                    
                    # Try to get website info
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
                    
                    all_properties.append(property_info)
    except Exception as e:
        print(f"❌ Error with Method 1: {str(e)}")
    
    # Method 2: Try to use searchGa4Properties (available in newer versions)
    try:
        print("\nMethod 2: Trying searchGa4Properties API...")
        
        # Check if method exists
        if not hasattr(analytics_admin, 'properties') or not hasattr(analytics_admin.properties(), 'searchGa4Properties'):
            print("❌ searchGa4Properties method not available in this API version")
        else:
            response = analytics_admin.properties().searchGa4Properties().execute()
            properties = response.get('ga4Properties', [])
            
            print(f"✅ Found {len(properties)} properties using searchGa4Properties")
            
            # Process each property
            for prop in properties:
                property_id = prop['name'].split('/')[-1]
                property_name = prop.get('displayName', 'Unnamed Property')
                account_id = prop.get('account', '').split('/')[-1]
                
                # Try to get account name
                account_name = "Unknown Account"
                try:
                    account_response = analytics_admin.accounts().get(
                        name=f"accounts/{account_id}"
                    ).execute()
                    account_name = account_response.get('displayName', 'Unknown Account')
                except:
                    pass
                
                # Add to our list if not already present
                if not any(p['property_id'] == property_id for p in all_properties):
                    property_info = {
                        'property_id': property_id,
                        'property_name': property_name,
                        'account_id': account_id,
                        'account_name': account_name,
                        'websites': [],
                        'source': 'search_ga4_properties'
                    }
                    
                    # Try to get website info
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
                    
                    all_properties.append(property_info)
    except AttributeError:
        print("❌ searchGa4Properties method not available in this API version")
    except Exception as e:
        print(f"❌ Error with Method 2: {str(e)}")
    
    # Method 3: Use direct property listing for each account
    try:
        print("\nMethod 3: Using direct property listing for each account...")
        
        # First get all accounts
        accounts_response = analytics_admin.accounts().list().execute()
        accounts = accounts_response.get('accounts', [])
        
        if not accounts:
            print("❌ No accounts found for direct property listing")
        else:
            print(f"✅ Found {len(accounts)} account(s) for direct property listing")
            
            # Process each account
            for account in accounts:
                account_id = account['name'].split('/')[-1]
                account_name = account.get('displayName', 'Unnamed Account')
                
                print(f"\nAccount: {account_name} (ID: {account_id})")
                
                # List properties directly
                try:
                    properties_response = analytics_admin.properties().list(
                        filter=f"parent:accounts/{account_id}"
                    ).execute()
                    properties = properties_response.get('properties', [])
                    
                    print(f"Found {len(properties)} properties through direct listing")
                    
                    for prop in properties:
                        property_id = prop['name'].split('/')[-1]
                        property_name = prop.get('displayName', 'Unnamed Property')
                        
                        # Add to our list if not already present
                        if not any(p['property_id'] == property_id for p in all_properties):
                            property_info = {
                                'property_id': property_id,
                                'property_name': property_name,
                                'account_id': account_id,
                                'account_name': account_name,
                                'websites': [],
                                'source': 'direct_listing'
                            }
                            
                            # Try to get website info
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
                            
                            all_properties.append(property_info)
                except Exception as e:
                    print(f"  Error listing properties for account {account_id}: {str(e)}")
    except Exception as e:
        print(f"❌ Error with Method 3: {str(e)}")
    
    # Summarize results
    print(f"\n=== RESULTS ===")
    print(f"Total properties found: {len(all_properties)}")
    
    # Save properties to CSV
    try:
        with open(OUTPUT_CSV, 'w', newline='') as csvfile:
            fieldnames = ['property_id', 'property_name', 'account_id', 'account_name', 'websites', 'source']
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
    
    # Print all properties
    if all_properties:
        print("\nAll properties found:")
        print("-" * 100)
        print(f"{'Property ID':<12} | {'Property Name':<35} | {'Account Name':<25} | {'Website':<20} | {'Source'}")
        print("-" * 100)
        
        for prop in all_properties:
            website = prop['websites'][0] if prop['websites'] else 'No website'
            print(f"{prop['property_id']:<12} | {prop['property_name'][:35]:<35} | {prop['account_name'][:25]:<25} | {website[:20]:<20} | {prop['source']}")
    
    return True

if __name__ == "__main__":
    main()