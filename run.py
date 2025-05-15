#!/usr/bin/env python
"""
Run script for GA4 Analytics Dashboard.
This script initializes and runs the Flask development server.
It loads environment variables from a .env file (if present)
and uses the application factory `create_app` from the `app` package.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file at the very beginning.
# This ensures that any environment variables used by Flask or extensions
# during initialization are already set.
load_dotenv()

from app import create_app  # Import the application factory

# Determine the configuration name from environment variables.
# Common choices are FLASK_CONFIG or FLASK_ENV.
# Fallback to 'development' if not set.
config_name = os.environ.get('FLASK_CONFIG') or os.environ.get('FLASK_ENV') or 'development'

# Create the Flask app instance using the factory and the determined configuration.
app = create_app(config_name)

if __name__ == '__main__':
    import argparse
    
    # Create the command-line argument parser
    parser = argparse.ArgumentParser(description='Run the GA4 Analytics Dashboard')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the server on')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Host to run the server on')
    args = parser.parse_args()
    
    # Get host and port from command line args or environment variables, with command line taking precedence
    host = args.host or os.environ.get('FLASK_RUN_HOST', '127.0.0.1')
    port = args.port or int(os.environ.get('FLASK_RUN_PORT', 5000))

    # The `debug` parameter for `app.run()` enables the Werkzeug debugger and reloader.
    # It's good practice to let the app's configuration (`app.config['DEBUG']`)
    # determine if debug mode should be active.
    # Flask's `app.run()` will use `app.debug` by default if `debug` is not explicitly passed.
    # Explicitly passing `app.debug` makes the intent clear.

    app.logger.info(f"Starting GA4 Analytics Dashboard application on http://{host}:{port}")
    app.logger.info(f"Application debug mode is: {app.debug}")

    # Run the Flask development server.
    # For production, use a WSGI server like Gunicorn:
    # Example: gunicorn --bind 0.0.0.0:5000 "run:app"
    app.run(host=host, port=port, debug=app.debug)