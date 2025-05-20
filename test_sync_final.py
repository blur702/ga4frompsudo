#!/usr/bin/env python3
"""Final test of OAuth2 property sync."""

import logging
from app import create_app
from app.services.ga4_service import GA4Service
from app.services.property_sync_service import PropertySyncService

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_sync():
    """Test property sync with OAuth2."""
    print("Testing Property Sync with OAuth2")
    print("=" * 40)
    
    # Create app context
    app = create_app()
    with app.app_context():
        db = app.database
        
        # Create services
        print("Initializing services...")
        ga4_service = GA4Service(auth_method='oauth2')
        sync_service = PropertySyncService(db, ga4_service)
        
        print(f"GA4 service available: {ga4_service.is_available()}")
        print(f"Auth method: {ga4_service.auth_method}")
        
        if ga4_service.is_available():
            print("\nStarting property sync...")
            try:
                results = sync_service.sync_all_properties(
                    fetch_websites=False,  # Skip website fetching to speed up
                    update_existing=True
                )
                
                print("\nSync Results:")
                print(f"Properties fetched: {results['properties_fetched']}")
                print(f"Properties created: {results['properties_created']}")
                print(f"Properties updated: {results['properties_updated']}")
                
                if results['errors']:
                    print(f"\nErrors: {len(results['errors'])}")
                    for error in results['errors'][:5]:
                        print(f"  - {error}")
                    
                print("\nDone!")
                
            except Exception as e:
                print(f"Error during sync: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("GA4 service not available")

if __name__ == "__main__":
    test_sync()