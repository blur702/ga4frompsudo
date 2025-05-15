"""
Application factory module.
Creates and configures the Flask application, initializes extensions,
and registers blueprints, error handlers, and context processors.
"""

import os
import datetime
import logging
from flask import Flask, render_template

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

    # Configure application logging using our utility function
    # We'll import locally to avoid circular imports
    from app.utils.logging_utils import configure_logging, log_exception
    
    # Determine config_name before using it
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    # Set up log directory structure
    log_dir = os.path.join(os.getcwd(), 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Create separate log files for different log levels
    error_log = os.path.join(log_dir, f"{config_name}_errors.log")
    app_log = os.path.join(log_dir, f"{config_name}.log") if config_name != 'testing' else None
    
    # Configure logging with error-only file logging and console for all levels
    logger = configure_logging(
        app_name='ga4_dashboard',
        log_level=os.environ.get('LOG_LEVEL', 'INFO'),
        log_file=app_log,
        log_to_console=True,
        file_log_level='INFO',    # Log INFO and above to main log file
        clear_log_file=True       # Clear log file on each run
    )
    
    # Configure a separate error log file that collects only errors and above
    error_handler = logging.FileHandler(error_log, 'w')  # 'w' mode to clear on startup
    error_handler.setLevel(logging.ERROR)
    error_format = '%(asctime)s %(levelname)s %(name)s [%(module)s.%(funcName)s:%(lineno)d]: %(message)s'
    error_handler.setFormatter(logging.Formatter(error_format, '%Y-%m-%d %H:%M:%S'))
    logger.addHandler(error_handler)
    
    # Log run separator for error log
    run_separator = f"\n{'='*80}\nAPPLICATION START: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n{'='*80}\n"
    with open(error_log, 'a') as f:
        f.write(run_separator)
        
    logger.info(f"Error logging configured to file: {error_log}")
    
    app.logger.info("Application factory `create_app` called.")

    app.logger.info(f"Attempting to load configuration: '{config_name}'")
    try:
        app.config.from_object(config[config_name])
        if hasattr(config[config_name], 'init_app'):
            config[config_name].init_app(app)  # Call init_app method of the chosen config class
        app.logger.info(f"Successfully configured application with '{config_name}' settings.")
    except KeyError:
        app.logger.error(f"Invalid configuration name: '{config_name}'. Falling back to 'default' configuration.")
        config_name = 'default'  # Ensure 'default' is a valid key in your config dict
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
    
    # Initialize utilities first as other components may depend on them
    from .utils import init_utils
    init_utils(app)
    
    # Initialize database
    from .models.database import Database  # Local import to avoid circular dependencies
    try:
        app.database = Database(app.config['DATABASE_PATH'])
        app.database.initialize()  # Creates tables if they don't exist
        app.logger.info(f"Database initialized at: {app.config['DATABASE_PATH']}")
    except Exception as e:
        app.logger.critical(f"CRITICAL: Failed to initialize database: {e}", exc_info=True)
        raise  # Re-raise critical error; app cannot function without DB

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
    
    # Import the services package
    from app.services import init_services as initialize_all_services, get_services
    
    # Initialize all services
    initialize_all_services(app)
    
    # Attach services to the app instance for easy access
    services = get_services()
    for name, service in services.items():
        service_attr_name = f"{name}_service"
        setattr(app, service_attr_name, service)
        app.logger.debug(f"Attached {name} service to app as '{service_attr_name}'")
    
    app.logger.info("Service initialization completed successfully")


def init_plugins(app):
    """
    Initialize and register plugins with the PluginService.
    Called from `init_extensions`.

    Args:
        app (Flask): The Flask application instance.
    """
    app.logger.info("Initializing and registering plugins...")
    
    # Get the plugin service
    from app.services import get_service
    plugin_service = get_service('plugin')
    
    if plugin_service:
        # Register all available plugins
        plugin_service.register_plugins()
        
        # Log discovered plugins
        available_plugins = plugin_service.get_available_plugins()
        app.logger.info(f"Registered {len(available_plugins)} plugins: {list(available_plugins.keys())}")
    else:
        app.logger.warning("Plugin service not available. Plugins will not be loaded.")
    
    app.logger.info("Plugin initialization completed")


def register_blueprints(app):
    """
    Register Flask blueprints for different parts of the application (e.g., API, web routes).

    Args:
        app (Flask): The Flask application instance.
    """
    app.logger.info("Registering application blueprints...")
    
    # Import controllers package
    from app.controllers import init_controllers
    
    # Initialize and register all controllers
    init_controllers(app)
    
    app.logger.info("Blueprint registration completed successfully")


def register_error_handlers(app):
    """
    Register custom error handlers for common HTTP errors.
    These handlers will render specific templates or return JSON responses for API errors.

    Args:
        app (Flask): The Flask application instance.
    """
    app.logger.info("Registering custom error handlers...")
    
    # Use our custom error handlers from the utils module
    from app.utils.error_handlers import register_error_handlers as register_utils_error_handlers
    register_utils_error_handlers(app)
    
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
        # Will be uncommented once the models are implemented
        # from . import models  # Assuming models are structured to be imported this way
        # context['models'] = models
        return context

    app.shell_context_processor(make_shell_context)
    app.logger.info("Shell context processor registered.")