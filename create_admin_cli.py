#!/usr/bin/env python3
"""
Admin User Creation Script (CLI version)

This script creates an admin user in the database taking arguments from command line.
It initializes the database connection and uses the proper model implementation.

Usage:
    python create_admin_cli.py <email> <password> [first_name] [last_name]
    
Example:
    python create_admin_cli.py admin@example.com password123 Admin User
"""

import os
import sys
import logging
import base64
from datetime import datetime

from app import create_app
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
        
        # Hash the password - returns a tuple of (hash, salt)
        hashed_password, salt = security_service.hash_password(password)
        
        # Convert binary hash and salt to a storable string format
        hash_base64 = base64.b64encode(hashed_password).decode('utf-8')
        salt_base64 = base64.b64encode(salt).decode('utf-8')
        # Create a combined string in the format used by auth_service.verify_password
        password_hash = f"{hash_base64}:{salt_base64}"
        
        # Check if user already exists
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
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <email> <password> [first_name] [last_name]")
        return 1
        
    email = sys.argv[1]
    password = sys.argv[2]
    first_name = sys.argv[3] if len(sys.argv) > 3 else "Admin"
    last_name = sys.argv[4] if len(sys.argv) > 4 else "User"
    
    # Validate inputs
    if not email or '@' not in email:
        print("Error: Invalid email format")
        return 1
        
    if not password:
        print("Error: Password cannot be empty")
        return 1
        
    if len(password) < 8:
        print("Error: Password must be at least 8 characters long")
        return 1
    
    # Create Flask app in development mode
    app = create_app('development')
    
    # Use app context
    with app.app_context():
        print(f"Creating admin user: {email}")
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