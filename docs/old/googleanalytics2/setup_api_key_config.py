"""
Script to apply the migration and set up the initial API key configuration.
"""
import os
import sys
from flask import Flask
from flask_migrate import Migrate
from modules.models import db, Setting
from modules.encryption import encrypt_value

def setup_api_key_config():
    """
    Apply the migration and set up the initial API key configuration.
    """
    # Create a Flask app
    app = Flask(__name__)
    app.config.from_object('config.Config')
    
    # Initialize the database
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config.get('DATABASE_URI', 'sqlite:///ga4_dashboard.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    
    # Initialize migrations
    migrate = Migrate(app, db)
    
    with app.app_context():
        # Create the is_encrypted column if it doesn't exist
        try:
            db.engine.execute("SELECT is_encrypted FROM setting LIMIT 1")
            print("The is_encrypted column already exists.")
        except Exception:
            print("Adding is_encrypted column to the setting table...")
            db.engine.execute("ALTER TABLE setting ADD COLUMN is_encrypted BOOLEAN NOT NULL DEFAULT 0")
            print("Column added successfully.")
        
        # Check if the google_api_key setting exists
        api_key_setting = Setting.query.filter_by(key='google_api_key').first()
        if not api_key_setting:
            print("Creating google_api_key setting...")
            Setting.set_value(
                'google_api_key',
                '',  # Empty initial value
                'Google API key for authentication',
                True  # Encrypted
            )
            print("Setting created successfully.")
        else:
            print("The google_api_key setting already exists.")
            
            # Update the setting to be encrypted if it's not already
            if not api_key_setting.is_encrypted:
                print("Updating google_api_key setting to be encrypted...")
                api_key_setting.is_encrypted = True
                db.session.commit()
                print("Setting updated successfully.")
        
        print("\nSetup completed successfully!")
        print("You can now configure your Google API key in the settings page.")

if __name__ == '__main__':
    setup_api_key_config()