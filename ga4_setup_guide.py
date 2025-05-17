#!/usr/bin/env python
"""
GA4 Setup Guide - Testing credentials and explaining required permissions
"""

import os
import json
import logging
import datetime
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

def print_setup_instructions():
    """Print instructions for setting up GA4 permissions"""
    print("\n" + "="*80)
    print("GA4 PERMISSIONS SETUP GUIDE".center(80))
    print("="*80 + "\n")
    
    print("The service account doesn't have access to any GA4 accounts. Follow these steps:\n")
    
    print("1. Identify your GA4 account")
    print("   - Log in to https://analytics.google.com/")
    print("   - Note your Account ID and Property ID from the Admin section\n")
    
    print("2. Grant access to your service account")
    print("   - Go to Admin > Account Access Management")
    print("   - Click the '+' button to add a new user")
    with open(CREDENTIALS_PATH) as f:
        creds_data = json.load(f)
        email = creds_data.get('client_email', 'YOUR_SERVICE_ACCOUNT_EMAIL')
        print(f"   - Enter the service account email: {email}")
    print("   - Select 'Viewer' role at minimum (or higher if needed)")
    print("   - Click 'Add'\n")
    
    print("3. Wait for permissions to propagate")
    print("   - It may take a few minutes for permissions to take effect\n")
    
    print("4. Run this script again to test access")
    print("   - Execute: python ga4_setup_guide.py\n")
    
    print("5. Troubleshooting:")
    print("   - Ensure the service account email is correct")
    print("   - Verify you have Admin access to grant permissions")
    print("   - Check that you're adding permissions to the correct GA4 account")
    print("   - You might need to grant permissions at both Account and Property levels\n")
    
    print("="*80)

def test_ga4_credentials():
    """Test if the GA4 credentials are valid and have correct permissions."""
    try:
        # Check if credentials file exists
        if not os.path.exists(CREDENTIALS_PATH):
            logger.error(f"Credentials file not found at {CREDENTIALS_PATH}")
            return False
        
        logger.info(f"Found credentials file at {CREDENTIALS_PATH}")
        
        # Display service account email
        with open(CREDENTIALS_PATH) as f:
            creds_data = json.load(f)
            email = creds_data.get('client_email')
            if email:
                logger.info(f"Using service account: {email}")
        
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
        
        if 'accountSummaries' in response and response['accountSummaries']:
            account_count = len(response['accountSummaries'])
            logger.info(f"SUCCESS: Retrieved {account_count} account(s)")
            
            # Show account details
            for account in response['accountSummaries']:
                account_id = account['account'].split('/')[-1]
                account_name = account.get('displayName', 'Unnamed Account')
                property_count = len(account.get('propertySummaries', []))
                
                logger.info(f"Account: {account_name} (ID: {account_id}) - {property_count} properties")
            
            return True
        else:
            logger.warning("No accounts found. The service account doesn't have access to any GA4 accounts.")
            return False
            
    except HttpError as e:
        logger.error(f"API error: {e.reason}")
        return False
    except Exception as e:
        logger.error(f"Error testing credentials: {str(e)}")
        return False

if __name__ == "__main__":
    try:
        # Check if the GA4 libraries are installed
        import google.oauth2.service_account
        import googleapiclient.discovery
    except ImportError:
        logger.error("Required Google libraries not installed. Run: pip install google-api-python-client google-auth")
        exit(1)
        
    print("\nTesting GA4 credentials...\n")
    
    # First test if credentials are valid
    success = test_ga4_credentials()
    
    if not success:
        # Print setup instructions
        print_setup_instructions()
    else:
        print("\n" + "="*80)
        print("GA4 CREDENTIALS TEST SUCCESSFUL".center(80))
        print("="*80 + "\n")
        print("Your service account has access to GA4 account(s).")
        print("You can now use the application to view your GA4 data.")
        print("\nTo get property information, run: python test_ga4_credentials.py")
        print("="*80 + "\n")