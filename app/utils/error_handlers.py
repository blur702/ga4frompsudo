"""
Error handling utilities for the application.
"""

import traceback
import logging
from flask import request, jsonify

logger = logging.getLogger(__name__)

def register_error_handlers(app):
    """
    Register error handlers with the Flask application.
    
    Args:
        app: Flask application instance
    """
    # Import log_exception function for enhanced error logging
    from app.utils.logging_utils import log_exception
    
    @app.errorhandler(Exception)
    def handle_unhandled_exception(error):
        """Handle all unhandled exceptions."""
        exc_info = (type(error), error, error.__traceback__)
        logger.error(
            f"Unhandled {error.__class__.__name__} exception: {str(error)}",
            exc_info=exc_info
        )
        
        # Write to a special errors-only log file
        error_logger = logging.getLogger('error')
        error_details = {
            'route': request.path,
            'method': request.method,
            'args': request.args.to_dict(),
            'headers': {k: v for k, v in request.headers.items() if k.lower() not in ('cookie', 'authorization')},
            'error_type': error.__class__.__name__,
            'error_msg': str(error),
            'traceback': traceback.format_exc()
        }
        error_logger.error(f"UNHANDLED EXCEPTION: {error_details}")
        
        # Check if this is an API request
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Internal server error',
                'message': str(error)
            }), 500
            
        # Render error template
        return render_template_with_logging('errors/500.html', 
                                          error=error, 
                                          status_code=500, 
                                          error_type=error.__class__.__name__), 500
    
    @app.errorhandler(500)
    def internal_server_error(error):
        """Handle internal server errors."""
        # Log details of the error
        logger.error(f"500 error on {request.path}: {error}")
        logger.error(traceback.format_exc())
        
        # Check if this is an API request
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Internal server error',
                'message': str(error)
            }), 500
        
        # Render error template for regular requests
        return render_template_with_logging('errors/500.html', error=error), 500

    @app.errorhandler(404)
    def page_not_found(error):
        """Handle page not found errors."""
        logger.warning(f"404 error on {request.path}: {error}")
        
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Not found',
                'message': 'The requested resource was not found'
            }), 404
        
        return render_template_with_logging('errors/404.html', error=error), 404

    @app.errorhandler(403)
    def forbidden(error):
        """Handle forbidden access errors."""
        logger.warning(f"403 error on {request.path}: {error}")
        
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Forbidden',
                'message': 'You do not have permission to access this resource'
            }), 403
        
        return render_template_with_logging('errors/403.html', error=error), 403

    @app.errorhandler(401)
    def unauthorized(error):
        """Handle unauthorized access errors."""
        logger.warning(f"401 error on {request.path}: {error}")
        
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Authentication is required to access this resource'
            }), 401
        
        return render_template_with_logging('errors/401.html', error=error), 401

def render_template_with_logging(template, **context):
    """
    Render a template with logging and fallback to basic HTML if template cannot be found.
    
    Args:
        template: The template to render
        **context: Template context variables
        
    Returns:
        Rendered template or basic HTML if template not found
    """
    from flask import render_template, current_app
    
    try:
        return render_template(template, **context)
    except Exception as e:
        logger.error(f"Error rendering template {template}: {e}")
        # Simple fallback for error pages
        error_title = context.get('error', 'Error')
        status_code = context.get('status_code', 500)
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{error_title}</title>
            <style>
                body {{ font-family: sans-serif; padding: 2rem; }}
                .error-container {{ max-width: 600px; margin: 0 auto; }}
                .error-code {{ font-size: 5rem; color: #dc3545; }}
                .error-message {{ font-size: 1.2rem; }}
            </style>
        </head>
        <body>
            <div class="error-container">
                <h1 class="error-code">{status_code}</h1>
                <h2>An error occurred</h2>
                <p class="error-message">{error_title}</p>
                <p><a href="/">Return to home page</a></p>
            </div>
        </body>
        </html>
        """