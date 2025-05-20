#!/usr/bin/env python3
"""Test OAuth2 setup and configuration."""

import os
from app import create_app
from app.models.app_settings import AppSettings
from app.services.ga4_service import GA4Service

def check_oauth2_setup():
    """Check the current OAuth2 setup and configuration."""
    print("Testing OAuth2 Setup")
    print("=" * 40)
    
    # Create app context
    app = create_app()
    with app.app_context():
        db = app.database
        
        # Check current auth method
        auth_method = AppSettings.get_setting(db, 'ga4_auth_method', 'service_account')
        print(f"Current auth method: {auth_method}")
        
        # Check OAuth2 configuration
        client_id = AppSettings.get_setting(db, 'oauth2_client_id')
        client_secret = AppSettings.get_setting(db, 'oauth2_client_secret')
        access_token = AppSettings.get_setting(db, 'oauth2_access_token')
        refresh_token = AppSettings.get_setting(db, 'oauth2_refresh_token')
        
        print(f"OAuth2 Client ID configured: {'Yes' if client_id else 'No'}")
        print(f"OAuth2 Client Secret configured: {'Yes' if client_secret else 'No'}")
        print(f"OAuth2 Access Token stored: {'Yes' if access_token else 'No'}")
        print(f"OAuth2 Refresh Token stored: {'Yes' if refresh_token else 'No'}")
        
        if client_id:
            print(f"Client ID (first 20 chars): {client_id[:20]}...")
        
        print("\nChecking GA4 service initialization...")
        
        # Initialize GA4 service with OAuth2
        try:
            ga4_service = GA4Service(auth_method='oauth2')
            print(f"GA4 service available: {ga4_service.is_available()}")
            
            if ga4_service.is_available():
                # Try to list properties
                print("\nAttempting to list properties with OAuth2...")
                properties = ga4_service.list_ga4_properties_with_details()
                print(f"Found {len(properties)} properties")
                
                for i, prop in enumerate(properties[:3]):  # Show first 3
                    print(f"\nProperty {i+1}:")
                    print(f"  Name: {prop.get('display_name')}")
                    print(f"  ID: {prop.get('property_id')}")
                    print(f"  Account: {prop.get('account_name')}")
            else:
                print("GA4 service is not available. OAuth2 flow may need to be completed.")
                
        except Exception as e:
            print(f"Error initializing GA4 service: {e}")
            
        print("\nNext Steps:")
        print("-" * 40)
        
        if not client_id or not client_secret:
            print("1. Go to the admin panel: http://localhost:5001/admin/ga4-config")
            print("2. Select OAuth2 authentication method")
            print("3. Enter your OAuth2 Client ID and Client Secret")
            print("4. The system will redirect you to Google for authorization")
        elif not access_token or not refresh_token:
            print("1. OAuth2 credentials are configured but authorization is incomplete")
            print("2. Go to: http://localhost:5001/admin/ga4-config")
            print("3. Click 'Authorize with Google' to complete the OAuth2 flow")
        else:
            print("OAuth2 is fully configured. If you're still having issues:")
            print("1. The tokens may have expired")
            print("2. Try re-authorizing through the admin panel")

if __name__ == "__main__":
    check_oauth2_setup()