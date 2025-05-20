#!/usr/bin/env python3
"""
Test script to verify the SQL error fix for Property.find_all()
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.database import Database
from app.models.property import Property
from app.models.website import Website
import logging

# Configure logging to see errors
logging.basicConfig(level=logging.INFO)

def test_property_find_all():
    """Test if Property.find_all() works without SQL errors."""
    print("Testing Property.find_all()...")
    
    # Initialize database
    db_path = "test_db.sqlite"
    db = Database(db_path)
    db.initialize()
    
    try:
        # Test Property.find_all()
        properties = Property.find_all(db, order_by="property_name ASC")
        print(f"Success! Found {len(properties)} properties")
        
        # Create a test property and find it
        test_prop = Property(
            database=db,
            property_id="properties/12345",
            property_name="Test Property"
        )
        test_prop.save()
        
        # Find again
        properties = Property.find_all(db, order_by="property_name ASC")
        print(f"After creating test property: Found {len(properties)} properties")
        
        # Test Website.find_all()
        websites = Website.find_all(db)
        print(f"Found {len(websites)} websites")
        
        print("\nAll tests passed! SQL error is fixed.")
        
    except Exception as e:
        print(f"Error occurred: {e}")
        print(f"Error type: {type(e)}")
        
    finally:
        # Clean up
        if os.path.exists(db_path):
            os.remove(db_path)

if __name__ == "__main__":
    test_property_find_all()