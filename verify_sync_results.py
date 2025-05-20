#!/usr/bin/env python3
"""Verify property sync results."""

from app import create_app
from app.models.property import Property

def verify_sync():
    """Verify property sync results."""
    print("Verifying Property Sync Results")
    print("=" * 40)
    
    # Create app context
    app = create_app()
    with app.app_context():
        db = app.database
        
        # Count properties in database
        properties = Property.find_all(db)
        print(f"Total properties in database: {len(properties)}")
        
        # Show first 10 properties
        print("\nFirst 10 properties:")
        for i, prop in enumerate(properties[:10]):
            print(f"{i+1}. {prop.property_name} (ID: {prop.property_id})")
            
        # Show properties by account
        accounts = {}
        for prop in properties:
            account_id = prop.account_id
            if account_id not in accounts:
                accounts[account_id] = []
            accounts[account_id].append(prop)
            
        print(f"\nProperties by account:")
        for account_id, props in list(accounts.items())[:5]:
            print(f"  Account {account_id}: {len(props)} properties")
        
        print(f"\nTotal accounts: {len(accounts)}")

if __name__ == "__main__":
    verify_sync()