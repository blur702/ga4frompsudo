#!/usr/bin/env python3
"""
Admin User Creation Script

This script creates an admin user in the database.
It initializes the database connection and uses the proper model implementation.
"""

import os
import sys
import logging
import getpass
from datetime import datetime

from flask import Flask
from app import create_app
from app.models.database import Database
from app.services.security_service import SecurityService

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_admin_user(app, email, password, first_name='Admin', last_name='User'):
    """
    Create an admin user in the database.

    Args:
        app: Flask application instance
        email: Admin user email
        password: Admin user password
        first_name: Admin user first name (default: 'Admin')
        last_name: Admin user last name (default: 'User')

    Returns:
        User ID if successful, None otherwise
    """
    try:
        # Get the database instance from the app
        database = app.database
        
        # Check if database is initialized
        if not database:
            logger.error("Database not initialized")
            return None

        # Initialize security service for password hashing
        security_config = {
            'key_path': app.config.get('SECURITY', {}).get('key_path') or os.path.join(os.path.abspath(os.path.dirname(__file__)), 'security', 'encryption_app.key'),
            'password_iterations': 310000
        }
        security_service = SecurityService(security_config)
        
        # Hash the password
        password_hash = security_service.hash_password(password)
        
        # Check if user already exists
        # First prepare a query to find the user by email
        query = "SELECT * FROM users WHERE email = ?"
        result = database.execute(query, (email,), fetchone=True)
        
        if result:
            logger.warning(f"User with email {email} already exists")
            return None
        
        # Get current timestamp in ISO format
        now = datetime.utcnow().isoformat()
            
        # Create user dictionary
        user_data = {
            'email': email,
            'password_hash': password_hash,
            'first_name': first_name,
            'last_name': last_name,
            'roles': 'admin',
            'is_active': 1,
            'created_at': now,
            'updated_at': now
        }
        
        # Insert user
        columns = ", ".join(user_data.keys())
        placeholders = ", ".join(["?"] * len(user_data))
        values = tuple(user_data.values())
        
        query = f"INSERT INTO users ({columns}) VALUES ({placeholders})"
        cursor = database.execute(query, values, commit=True)
        
        user_id = cursor.lastrowid
        logger.info(f"Admin user created with ID: {user_id}")
        
        return user_id
        
    except Exception as e:
        logger.error(f"Error creating admin user: {e}", exc_info=True)
        return None

def main():
    """Main function to create an admin user."""
    # Create Flask app in development mode
    app = create_app('development')
    
    # Use app context
    with app.app_context():
        print("=== GA4 Analytics Dashboard Admin Creation ===")
        
        # Get admin details
        email = input("Enter admin email: ").strip()
        password = getpass.getpass("Enter admin password: ").strip()
        confirm_password = getpass.getpass("Confirm password: ").strip()
        
        # Validate inputs
        if not email or '@' not in email:
            print("Error: Invalid email format")
            return 1
            
        if not password:
            print("Error: Password cannot be empty")
            return 1
            
        if password != confirm_password:
            print("Error: Passwords do not match")
            return 1
            
        if len(password) < 8:
            print("Error: Password must be at least 8 characters long")
            return 1
        
        # Create admin user
        first_name = input("Enter first name [Admin]: ").strip() or "Admin"
        last_name = input("Enter last name [User]: ").strip() or "User"
        
        print(f"\nCreating admin user: {email}")
        user_id = create_admin_user(app, email, password, first_name, last_name)
        
        if user_id:
            print(f"Admin user created successfully with ID: {user_id}")
            print("You can now log in to the application with this user.")
            return 0
        else:
            print("Failed to create admin user. Check logs for details.")
            return 1

if __name__ == "__main__":
    sys.exit(main())