#!/usr/bin/env python
"""
Test script to validate GA4 credentials and retrieve property information.
This script tests if the credentials have the correct permissions to access
GA4 properties and their associated websites.
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

def test_ga4_credentials():
    """Test if the GA4 credentials are valid and have correct permissions."""
    try:
        # Check if credentials file exists
        if not os.path.exists(CREDENTIALS_PATH):
            logger.error(f"Credentials file not found at {CREDENTIALS_PATH}")
            return False
        
        logger.info(f"Found credentials file at {CREDENTIALS_PATH}")
        
        # Initialize credentials
        scopes = ['https://www.googleapis.com/auth/analytics.readonly']
        credentials = Credentials.from_service_account_file(
            CREDENTIALS_PATH, scopes=scopes
        )
        
        # Initialize Admin API service
        analytics_admin = build('analyticsadmin', 'v1beta', credentials=credentials)
        admin = analytics_admin.accountSummaries()
        
        # Test API access by listing account summaries
        logger.info("Testing API access by listing account summaries...")
        response = admin.list().execute()
        
        if 'accountSummaries' in response:
            account_count = len(response['accountSummaries'])
            logger.info(f"Successfully retrieved {account_count} account(s)")
            return True
        else:
            logger.warning("No accounts found. User might not have access to any GA4 accounts.")
            return False
            
    except HttpError as e:
        logger.error(f"API error: {e.reason}")
        return False
    except Exception as e:
        logger.error(f"Error testing credentials: {str(e)}")
        return False

def get_property_information():
    """
    Retrieve property IDs, names, and websites for all accessible GA4 properties.
    Returns a list of dictionaries with property details.
    """
    try:
        # Initialize credentials
        scopes = ['https://www.googleapis.com/auth/analytics.readonly']
        credentials = Credentials.from_service_account_file(
            CREDENTIALS_PATH, scopes=scopes
        )
        
        # Initialize Admin API service for property information
        analytics_admin = build('analyticsadmin', 'v1beta', credentials=credentials)
        
        # Initialize Data API service for website information
        analytics_data = build('analyticsdata', 'v1beta', credentials=credentials)
        
        # Get account summaries
        accounts_response = analytics_admin.accountSummaries().list().execute()
        
        if 'accountSummaries' not in accounts_response:
            logger.warning("No accounts found")
            return []
        
        properties_info = []
        
        # Process each account
        for account in accounts_response['accountSummaries']:
            account_id = account['account'].split('/')[-1]
            account_name = account.get('displayName', 'Unnamed Account')
            
            logger.info(f"Processing account: {account_name} (ID: {account_id})")
            
            # Process properties in this account
            for property_summary in account.get('propertySummaries', []):
                property_id = property_summary['property'].split('/')[-1]
                property_name = property_summary.get('displayName', 'Unnamed Property')
                
                logger.info(f"  Found property: {property_name} (ID: {property_id})")
                
                # Get data streams (websites) for this property
                try:
                    streams_response = analytics_admin.properties().dataStreams().list(
                        parent=f"properties/{property_id}"
                    ).execute()
                    
                    websites = []
                    for stream in streams_response.get('dataStreams', []):
                        if stream.get('webStreamData'):
                            websites.append(stream.get('webStreamData', {}).get('defaultUri', 'Unknown'))
                    
                    logger.info(f"    Found {len(websites)} website(s) for this property")
                    
                    # Add property info to our results
                    properties_info.append({
                        'account_id': account_id,
                        'account_name': account_name,
                        'property_id': property_id,
                        'property_name': property_name,
                        'websites': websites
                    })
                    
                except HttpError as e:
                    logger.error(f"    Error getting streams for property {property_id}: {e.reason}")
                except Exception as e:
                    logger.error(f"    Error processing property {property_id}: {str(e)}")
        
        return properties_info
        
    except HttpError as e:
        logger.error(f"API error: {e.reason}")
        return []
    except Exception as e:
        logger.error(f"Error retrieving property information: {str(e)}")
        return []

if __name__ == "__main__":
    # First test if credentials are valid
    if test_ga4_credentials():
        logger.info("Credentials test passed. Proceeding to fetch property information...")
        
        # Get property information
        properties = get_property_information()
        
        # Display results
        if properties:
            logger.info(f"Successfully retrieved information for {len(properties)} properties")
            print("\nProperty Information:")
            print("====================")
            
            for prop in properties:
                print(f"\nAccount: {prop['account_name']} (ID: {prop['account_id']})")
                print(f"Property: {prop['property_name']} (ID: {prop['property_id']})")
                print("Websites:")
                if prop['websites']:
                    for website in prop['websites']:
                        print(f"  - {website}")
                else:
                    print("  No websites found")
            
            # Save to JSON file for future use
            with open('ga4_properties.json', 'w') as f:
                json.dump(properties, f, indent=2)
            logger.info("Property information saved to ga4_properties.json")
        else:
            logger.warning("No properties were found or could be accessed")
    else:
        logger.error("Credentials test failed. Please check your credentials and permissions.")