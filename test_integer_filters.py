#!/usr/bin/env python3
"""
Test script to verify that BaseModel.find_all() correctly handles integer parameters in filters.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.database import Database
from app.models.property import Property
import logging
import json
import datetime

# Configure logging to see errors
logging.basicConfig(level=logging.INFO)

def test_integer_filters():
    """Test if find_all() correctly handles integer values in filters."""
    print("Testing integer filters in find_all()...")
    
    # Initialize database
    db_path = "test_integer_filters.sqlite"
    db = Database(db_path)
    db.initialize()
    
    try:
        # Create test properties
        # First property
        property1 = Property(
            database=db,
            property_id="properties/123456",
            property_name="Test Property 1",
            account_id="accounts/1234",
            create_time=datetime.datetime.now(),
            update_time=datetime.datetime.now()
        )
        property1.save()
        print(f"Created property 1 with ID: {property1.id}")
        
        # Second property
        property2 = Property(
            database=db,
            property_id="properties/789012",
            property_name="Test Property 2",
            account_id="accounts/5678",
            create_time=datetime.datetime.now(),
            update_time=datetime.datetime.now()
        )
        property2.save()
        print(f"Created property 2 with ID: {property2.id}")
        
        # Test finding a property by ID using integer filter
        # This is the key test for integer parameters
        print("\nTesting find_all with integer filter for ID...")
        property_id_to_find = property1.id
        properties = Property.find_all(db, filters={'id': property_id_to_find})
        
        if properties and len(properties) == 1 and properties[0].id == property_id_to_find:
            print(f"✓ Successfully found property with ID {property_id_to_find} using integer filter")
        else:
            print(f"✗ Failed to find property with ID {property_id_to_find} using integer filter")
            print(f"Found properties: {properties}")
        
        # Also test with string filters for completeness
        print("\nTesting find_all with string filter for account_id...")
        account_id_to_find = "accounts/1234"
        properties = Property.find_all(db, filters={'account_id': account_id_to_find})
        
        if properties and len(properties) == 1 and properties[0].account_id == account_id_to_find:
            print(f"✓ Successfully found property with account_id '{account_id_to_find}' using string filter")
        else:
            print(f"✗ Failed to find property with account_id '{account_id_to_find}' using string filter")
            print(f"Found properties: {properties}")
        
        # Test limit and offset integer parameters
        print("\nTesting find_all with integer limit and offset parameters...")
        # Should return just one property with limit=1
        properties_limited = Property.find_all(db, limit=1)
        if properties_limited and len(properties_limited) == 1:
            print("✓ Successfully applied integer limit=1")
        else:
            print(f"✗ Failed to apply integer limit=1. Found: {len(properties_limited) if properties_limited else 0} properties")
        
        # Should return the second property with offset=1
        properties_offset = Property.find_all(db, offset=1, limit=1)
        if properties_offset and len(properties_offset) == 1 and properties_offset[0].id == property2.id:
            print("✓ Successfully applied integer offset=1")
        else:
            print(f"✗ Failed to apply integer offset=1")
            if properties_offset:
                print(f"Found property with ID: {properties_offset[0].id}, expected: {property2.id}")
        
        print("\nAll integer filter tests completed.")
        
    except Exception as e:
        print(f"Error occurred: {e}")
        print(f"Error type: {type(e)}")
        
    finally:
        # Clean up
        if os.path.exists(db_path):
            os.remove(db_path)

if __name__ == "__main__":
    test_integer_filters()