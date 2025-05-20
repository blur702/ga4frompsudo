#!/usr/bin/env python3
"""Simple test of OAuth2 property listing."""

import logging
from app import create_app
from app.models.app_settings import AppSettings
from app.services.ga4_service import GA4Service

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_oauth2_properties():
    """Test OAuth2 property listing."""
    print("Testing OAuth2 Property Listing")
    print("=" * 40)
    
    # Create app context
    app = create_app()
    with app.app_context():
        db = app.database
        
        # Check OAuth2 tokens
        access_token = AppSettings.get_setting(db, 'oauth2_access_token')
        refresh_token = AppSettings.get_setting(db, 'oauth2_refresh_token')
        
        print(f"Access token exists: {bool(access_token)}")
        print(f"Refresh token exists: {bool(refresh_token)}")
        
        if access_token and refresh_token:
            print("\nCreating GA4 service...")
            ga4_service = GA4Service(auth_method='oauth2')
            
            print(f"Service available: {ga4_service.is_available()}")
            
            if ga4_service.is_available():
                print("\nTesting list_account_summaries...")
                try:
                    accounts = ga4_service.list_account_summaries()
                    print(f"Found {len(accounts)} accounts")
                    for account in accounts[:3]:
                        print(f"  Account: {account.get('displayName')} ({account.get('name')})")
                except Exception as e:
                    print(f"Error listing accounts: {e}")
                    
                print("\nTesting list_properties...")
                try:
                    properties = ga4_service.list_properties()
                    print(f"Found {len(properties)} properties")
                    for prop in properties[:5]:
                        print(f"  Property: {prop.get('displayName')} ({prop.get('name')})")
                except Exception as e:
                    print(f"Error listing properties: {e}")
                    
                print("\nDone!")
            else:
                print("GA4 service not available")
        else:
            print("\nNo OAuth2 tokens found. Please complete OAuth2 flow first.")

if __name__ == "__main__":
    test_oauth2_properties()