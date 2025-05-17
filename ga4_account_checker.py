#!/usr/bin/env python
"""
GA4 Account Checker - Identify available GA4 accounts and provide detailed steps
for setting up property access.
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

def get_client_email():
    """Get the service account email from credentials file"""
    with open(CREDENTIALS_PATH) as f:
        creds_data = json.load(f)
        return creds_data.get('client_email', 'Unknown')

def check_ga4_accounts():
    """Check what GA4 accounts the service account has access to"""
    try:
        # Initialize credentials
        scopes = ['https://www.googleapis.com/auth/analytics.readonly']
        credentials = Credentials.from_service_account_file(
            CREDENTIALS_PATH, scopes=scopes
        )
        
        # Initialize Admin API service
        analytics_admin = build('analyticsadmin', 'v1beta', credentials=credentials)
        admin = analytics_admin.accountSummaries()
        
        # Get account summaries
        logger.info("Fetching GA4 account summaries...")
        response = admin.list().execute()
        
        if 'accountSummaries' in response and response['accountSummaries']:
            accounts = response['accountSummaries']
            logger.info(f"Found {len(accounts)} GA4 account(s)")
            return accounts
        else:
            logger.warning("No GA4 accounts found. The service account has API access but no account permissions.")
            return []
            
    except HttpError as e:
        logger.error(f"API error: {e.reason}")
        return []
    except Exception as e:
        logger.error(f"Error checking GA4 accounts: {str(e)}")
        return []

def list_empty_accounts():
    """List accounts without properties or access to properties"""
    accounts = check_ga4_accounts()
    
    if not accounts:
        print("\nNo GA4 accounts found for this service account.")
        print("You need to give the service account access to your GA4 account in the Google Analytics Admin console.")
        return
    
    empty_accounts = []
    accounts_with_properties = []
    
    # Check each account for properties
    for account in accounts:
        account_id = account['account'].split('/')[-1]
        account_name = account.get('displayName', 'Unnamed Account')
        
        if 'propertySummaries' not in account or not account['propertySummaries']:
            empty_accounts.append((account_id, account_name))
        else:
            accounts_with_properties.append((account_id, account_name, len(account['propertySummaries'])))
    
    # Print results
    print("\n" + "="*80)
    print("GA4 ACCOUNTS ACCESS SUMMARY".center(80))
    print("="*80 + "\n")
    
    print(f"Service Account: {get_client_email()}")
    print(f"Total GA4 Accounts with access: {len(accounts)}")
    
    if accounts_with_properties:
        print("\nAccounts WITH properties access:")
        for account_id, account_name, prop_count in accounts_with_properties:
            print(f"✅ {account_name} (ID: {account_id}) - {prop_count} properties")
            
            # Try to list properties for this account
            try:
                # Re-initialize credentials and service
                scopes = ['https://www.googleapis.com/auth/analytics.readonly']
                credentials = Credentials.from_service_account_file(
                    CREDENTIALS_PATH, scopes=scopes
                )
                analytics_admin = build('analyticsadmin', 'v1beta', credentials=credentials)
                
                # Get a specific account
                for account in accounts:
                    if account['account'].split('/')[-1] == account_id:
                        # List properties
                        for prop in account.get('propertySummaries', []):
                            property_id = prop['property'].split('/')[-1]
                            property_name = prop.get('displayName', 'Unnamed Property')
                            print(f"   - Property: {property_name} (ID: {property_id})")
                            
                            # Try to get data streams
                            try:
                                streams_response = analytics_admin.properties().dataStreams().list(
                                    parent=f"properties/{property_id}"
                                ).execute()
                                
                                for stream in streams_response.get('dataStreams', []):
                                    stream_id = stream['name'].split('/')[-1]
                                    stream_type = next((k for k in stream if k.endswith('StreamData')), None)
                                    
                                    if stream_type == 'webStreamData':
                                        uri = stream.get('webStreamData', {}).get('defaultUri', 'Unknown')
                                        print(f"      - Website: {uri} (ID: {stream_id})")
                                    else:
                                        name = stream.get('displayName', 'Unnamed Stream')
                                        print(f"      - Stream: {name} (ID: {stream_id}, Type: {stream_type})")
                            except HttpError as e:
                                if e.resp.status == 403:
                                    print(f"      ⚠️ Cannot access streams - insufficient permissions")
                                else:
                                    print(f"      ⚠️ Error getting streams: {e.reason}")
            except Exception as e:
                print(f"   ⚠️ Error listing properties: {str(e)}")
    
    if empty_accounts:
        print("\nAccounts WITHOUT properties access:")
        for account_id, account_name in empty_accounts:
            print(f"❌ {account_name} (ID: {account_id}) - No properties or no access to properties")
    
    print("\n" + "="*80)
    print("NEXT STEPS".center(80))
    print("="*80 + "\n")
    
    if not accounts_with_properties:
        print("The service account doesn't have access to any GA4 properties. You need to:")
        
        if accounts:
            print(f"1. Go to GA4 Admin > Property Access Management for your property")
            print(f"2. Add the service account email as a user:")
            print(f"   {get_client_email()}")
            print(f"3. Grant at least 'Viewer' role")
        else:
            print(f"1. Go to GA4 Admin > Account Access Management")
            print(f"2. Add the service account email as a user:")
            print(f"   {get_client_email()}")
            print(f"3. Grant at least 'Viewer' role")
            print(f"4. Then add access to specific properties")
    else:
        print("To access any properties marked with ⚠️, you need to:")
        print(f"1. Go to GA4 Admin > Property Access Management for that property")
        print(f"2. Add the service account email as a user:")
        print(f"   {get_client_email()}")
        print(f"3. Grant at least 'Viewer' role")
    
    print("\nAfter adding permissions, wait a few minutes and run this script again to verify access.")
    print("="*80)

if __name__ == "__main__":
    list_empty_accounts()