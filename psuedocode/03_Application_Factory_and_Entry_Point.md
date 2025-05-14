# 03 - Application Factory and Entry Point

This file details the pseudocode for the application factory (`app/__init__.py`) and the application entry point (`run.py`).

## 1. Application Factory

Target file: `app/__init__.py`

### Pseudocode (from `app-initialization-pseudocode.md`, refined in previous turns)

```python
"""
Application factory module.
Creates and configures the Flask application, initializes extensions,
and registers blueprints, error handlers, and context processors.
"""

import os
import datetime
import logging
from flask import Flask, render_template # render_template for error pages

# Import config dictionary from the config module
from .config import config

# Other imports (e.g., for models, services, plugins) will be done locally
# within initialization functions to manage dependencies and avoid circular imports.

def create_app(config_name=None):
    """
    Create and configure the Flask application instance.

    This function acts as the application factory. It sets up the configuration,
    initializes extensions (like database, services), registers blueprints,
    error handlers, context processors, and shell commands.

    Args:
        config_name (str, optional): The name of the configuration to use
                                     (e.g., 'development', 'testing', 'production').
                                     If None, it defaults to the value of the
                                     FLASK_ENV environment variable, or 'development'.

    Returns:
        Flask: The configured Flask application instance.
    """
    app = Flask(__name__, instance_relative_config=False)

    # Configure application logging
    # This basicConfig sets up logging to the console.
    # For production, more advanced logging (e.g., to files, with rotation) is recommended.
    log_level_str = os.environ.get('LOG_LEVEL', 'INFO').upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    logging.basicConfig(level=log_level,
                        format='%(asctime)s %(levelname)s %(name)s [%(module)s.%(funcName)s:%(lineno)d]: %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    app.logger.info("Application factory `create_app` called.")


    # Load configuration
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app.logger.info(f"Attempting to load configuration: '{config_name}'")
    try:
        app.config.from_object(config[config_name])
        if hasattr(config[config_name], 'init_app'):
            config[config_name].init_app(app) # Call init_app method of the chosen config class
        app.logger.info(f"Successfully configured application with '{config_name}' settings.")
    except KeyError:
        app.logger.error(f"Invalid configuration name: '{config_name}'. Falling back to 'default' configuration.")
        config_name = 'default' # Ensure 'default' is a valid key in your config dict
        app.config.from_object(config[config_name])
        if hasattr(config[config_name], 'init_app'):
            config[config_name].init_app(app)

    # Initialize extensions (Database, Services, Plugins)
    # This needs the app context to be available for extensions that require it.
    with app.app_context():
        init_extensions(app)

    # Register blueprints for routing
    register_blueprints(app)

    # Register custom error handlers
    register_error_handlers(app)

    # Register context processors for templates
    register_context_processors(app)

    # Register shell context for `flask shell`
    register_shell_context(app)

    app.logger.info(f"GA4 Analytics Dashboard application instance created successfully with '{config_name}' configuration.")
    return app

def init_extensions(app):
    """
    Initialize Flask extensions and application-specific components like the database.
    This function is called within the application context from `create_app`.

    Args:
        app (Flask): The Flask application instance.
    """
    app.logger.info("Initializing extensions...")
    from .models.database import Database # Local import to avoid circular dependencies
    try:
        app.database = Database(app.config['DATABASE_PATH'])
        app.database.initialize() # Creates tables if they don't exist
        app.logger.info(f"Database initialized at: {app.config['DATABASE_PATH']}")
    except Exception as e:
        app.logger.critical(f"CRITICAL: Failed to initialize database: {e}", exc_info=True)
        raise # Re-raise critical error; app cannot function without DB

    # Initialize services (which often depend on config and database)
    init_services(app)

    # Initialize plugins (which might depend on services like GA4Service or Database)
    init_plugins(app)
    app.logger.info("Extensions initialization process completed.")


def init_services(app):
    """
    Initialize application services and attach them to the app instance.
    Called from `init_extensions`.

    Args:
        app (Flask): The Flask application instance.
    """
    app.logger.info("Initializing application services...")
    # Import services locally to manage dependencies and avoid premature imports
    from .services.auth_service import AuthService
    from .services.ga4_service import GA4Service
    from .services.plugin_service import PluginService
    from .services.report_service import ReportService
    from .services.security_service import SecurityService

    try:
        # Order of initialization might matter if services depend on each other
        app.security_service = SecurityService(app.config.get('SECURITY', {}))
        app.logger.debug("SecurityService initialized.")

        # Assuming AuthService might use SecurityService for token operations
        app.auth_service = AuthService(app.config.get('AUTH', {}), app.security_service)
        app.logger.debug("AuthService initialized.")

        app.ga4_service = GA4Service(app.auth_service) # GA4Service depends on AuthService
        app.logger.debug("GA4Service initialized.")

        app.plugin_service = PluginService()
        app.logger.debug("PluginService initialized.")

        # ReportService depends on Database, GA4Service, and PluginService
        app.report_service = ReportService(app.database, app.ga4_service, app.plugin_service)
        app.logger.debug("ReportService initialized.")

        app.logger.info("All services initialized successfully.")
    except Exception as e:
        app.logger.critical(f"CRITICAL: Failed to initialize one or more services: {e}", exc_info=True)
        raise # Services are critical


def init_plugins(app):
    """
    Initialize and register plugins with the PluginService.
    Called from `init_extensions`.

    Args:
        app (Flask): The Flask application instance.
    """
    app.logger.info("Initializing and registering plugins...")
    # Import plugin utilities locally
    from .plugins import get_all_plugins, AVAILABLE_PLUGINS

    try:
        # get_all_plugins should instantiate plugins, passing necessary dependencies
        app.plugins_store = get_all_plugins(ga4_service=app.ga4_service, database=app.database)
        app.logger.info(f"Instantiated plugins: {list(app.plugins_store.keys())}")

        # Register each plugin instance's class with the plugin service
        for plugin_type, plugin_instance in app.plugins_store.items():
            if plugin_type in AVAILABLE_PLUGINS: # Ensure we only register known/expected plugin types
                 app.plugin_service.register_plugin(plugin_type, plugin_instance.__class__) # Register the class
                 app.logger.debug(f"Registered plugin class for type: {plugin_type}")
            else:
                app.logger.warning(f"Plugin type '{plugin_type}' found but not in AVAILABLE_PLUGINS. Skipping registration.")
        app.logger.info("Plugins initialized and registered with PluginService.")
    except Exception as e:
        app.logger.error(f"Failed to initialize or register plugins: {e}", exc_info=True)
        # Depending on requirements, this might not be a critical error if plugins are optional.
        pass


def register_blueprints(app):
    """
    Register Flask blueprints for different parts of the application (e.g., API, web routes).
    This is a placeholder; actual blueprints will be imported and registered
    once controller modules are defined.

    Args:
        app (Flask): The Flask application instance.
    """
    app.logger.info("Registering blueprints (placeholder)...")
    # Example structure when controllers are defined:
    # from .controllers.auth_routes import auth_bp # Assuming auth_routes.py defines 'auth_bp'
    # app.register_blueprint(auth_bp, url_prefix='/auth')

    # from .controllers.dashboard_routes import dashboard_bp
    # app.register_blueprint(dashboard_bp) # No prefix, routes defined from '/'

    # Based on original pseudocode structure for API and Web:
    # from app.controllers.api import api_bp # if controllers/api.py defines api_bp
    # app.register_blueprint(api_bp, url_prefix='/api')
    # from app.controllers.web import web_bp # if controllers/web.py defines web_bp
    # app.register_blueprint(web_bp)
    app.logger.info("Blueprint registration needs actual implementation when controller modules are created.")


def register_error_handlers(app):
    """
    Register custom error handlers for common HTTP errors.
    These handlers will render specific templates or return JSON responses for API errors.

    Args:
        app (Flask): The Flask application instance.
    """
    app.logger.info("Registering custom error handlers...")

    @app.errorhandler(404)
    def page_not_found_error(error): # Renamed variable to avoid conflict
        """Handles 404 Not Found errors."""
        app.logger.warning(f"Not Found (404): {error.description if hasattr(error, 'description') else str(error)} - Path: {getattr(error, 'request_path', 'N/A')}")
        # In a real app, you'd render a template:
        # return render_template('errors/404.html', error=error), 404
        return "<h3>404 - Page Not Found</h3><p>Sorry, the page you are looking for does not exist.</p>", 404

    @app.errorhandler(500)
    def internal_server_error_handler(error): # Renamed variable
        """Handles 500 Internal Server errors."""
        app.logger.error(f"Internal Server Error (500): {error}", exc_info=True) # Log the full exception
        # return render_template('errors/500.html', error=error), 500
        return "<h3>500 - Internal Server Error</h3><p>An unexpected error occurred on our server. We are investigating.</p>", 500

    @app.errorhandler(403)
    def forbidden_error(error): # Renamed variable
        """Handles 403 Forbidden errors."""
        app.logger.warning(f"Forbidden (403): {error.description if hasattr(error, 'description') else str(error)}")
        # return render_template('errors/403.html', error=error), 403
        return "<h3>403 - Forbidden</h3><p>You do not have the necessary permissions to access this resource.</p>", 403

    @app.errorhandler(401)
    def unauthorized_error(error): # Renamed variable
        """Handles 401 Unauthorized errors."""
        app.logger.warning(f"Unauthorized (401): {error.description if hasattr(error, 'description') else str(error)}")
        # return render_template('errors/401.html', error=error), 401
        # Could also redirect to login page:
        # from flask import redirect, url_for
        # return redirect(url_for('auth_bp.login_route_name_here')) # Example
        return "<h3>401 - Unauthorized</h3><p>Authentication is required to access this resource. Please log in.</p>", 401
    app.logger.info("Custom error handlers registered.")


def register_context_processors(app):
    """
    Register context processors to inject variables into templates globally.
    These variables are then available in all rendered Jinja2 templates.

    Args:
        app (Flask): The Flask application instance.
    """
    app.logger.info("Registering context processors...")
    @app.context_processor
    def inject_global_template_vars():
        """Injects global variables into the template context."""
        return {
            'app_name': app.config.get('APP_NAME', 'GA4 Analytics Dashboard'),
            'current_year': datetime.datetime.now(datetime.timezone.utc).year
        }
    app.logger.info("Context processors registered.")


def register_shell_context(app):
    """
    Register a shell context processor for the Flask CLI shell (`flask shell`).
    This makes specified variables automatically available in the interactive shell.

    Args:
        app (Flask): The Flask application instance.
    """
    app.logger.info("Registering shell context processor...")
    def make_shell_context():
        """Creates the context dictionary for the Flask shell."""
        context = {'app': app}
        # Dynamically add attached services and database to the context if they exist on the app object
        for attr_name in ['database', 'auth_service', 'ga4_service', 'plugin_service', 'report_service', 'security_service']:
            if hasattr(app, attr_name):
                context[attr_name] = getattr(app, attr_name)

        # Optionally, add models for easier debugging in the shell
        from . import models # Assuming models are structured to be imported this way
        context['models'] = models
        # Example: from .models.property import Property
        # context['Property'] = Property
        return context

    app.shell_context_processor(make_shell_context)
    app.logger.info("Shell context processor registered.")

    """
Application entry point.
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

from app import create_app # Import the application factory

# Determine the configuration name from environment variables.
# Common choices are FLASK_CONFIG or FLASK_ENV.
# Fallback to 'development' if not set.
config_name = os.environ.get('FLASK_CONFIG') or os.environ.get('FLASK_ENV') or 'development'

# Create the Flask app instance using the factory and the determined configuration.
app = create_app(config_name)

if __name__ == '__main__':
    # Get host and port from environment variables for app.run(), or use defaults.
    # These are typically for the development server.
    # In production, a proper WSGI server (like Gunicorn or uWSGI) would be used.
    host = os.environ.get('FLASK_RUN_HOST', '127.0.0.1') # Default to loopback for local dev
    port = int(os.environ.get('FLASK_RUN_PORT', 5000))

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
    app.run(host=host, port=port)
```
