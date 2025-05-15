"""
Admin controller for handling admin-specific functionality.
"""

import os
import json
import logging
from flask import Blueprint, request, redirect, url_for, flash, render_template, current_app, jsonify

from app.controllers.auth_controller import admin_required
from app.services import get_service
from app.services.ga4_service import GA4Service

logger = logging.getLogger(__name__)

# Create blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
@admin_required
def index():
    """Admin dashboard."""
    return render_template('admin/index.html')

@admin_bp.route('/ga4-config', methods=['GET', 'POST'])
@admin_required
def ga4_config():
    """
    Configure GA4 API credentials.
    
    GET: Display the GA4 configuration form
    POST: Process the GA4 configuration form submission
    """
    # Get the config path from app config
    credentials_path = current_app.config.get('GA4_CREDENTIALS_PATH')
    credentials_exist = credentials_path and os.path.exists(credentials_path)
    
    # Get existing credentials if they exist
    existing_credentials = {}
    if credentials_exist:
        try:
            with open(credentials_path, 'r') as f:
                existing_credentials = json.load(f)
                # Mask sensitive data for display
                if 'private_key' in existing_credentials:
                    existing_credentials['private_key'] = '********MASKED********'
        except Exception as e:
            logger.error(f"Error reading existing GA4 credentials: {e}")
            flash('Unable to read existing GA4 credentials file. It may be corrupted.', 'warning')
    
    # Handle form submission
    if request.method == 'POST':
        submission_method = request.form.get('submission_method', '')
        
        # Handle JSON input
        if submission_method == 'json':
            credentials_json = request.form.get('credentials_json', '').strip()
            if not credentials_json:
                flash('GA4 credentials JSON is required', 'error')
                return render_template('admin/ga4_config.html', 
                                      credentials_exist=credentials_exist,
                                      existing_credentials=existing_credentials)
            
            try:
                # Validate JSON
                json_data = json.loads(credentials_json)
                required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 
                                  'client_email', 'client_id', 'token_uri']
                missing_fields = [field for field in required_fields if field not in json_data]
                
                if missing_fields:
                    flash(f'The following required fields are missing from your credentials: {", ".join(missing_fields)}', 'error')
                    return render_template('admin/ga4_config.html', 
                                          credentials_exist=credentials_exist,
                                          existing_credentials=existing_credentials)
                
                # Create credentials directory if it doesn't exist
                credentials_dir = os.path.dirname(credentials_path)
                if not os.path.exists(credentials_dir):
                    os.makedirs(credentials_dir)
                
                # Write credentials to file
                with open(credentials_path, 'w') as f:
                    f.write(credentials_json)
                
                # Reinitialize GA4 service
                ga4_service = GA4Service(credentials_path=credentials_path)
                app_services = current_app.services if hasattr(current_app, 'services') else None
                if app_services:
                    app_services['ga4'] = ga4_service
                setattr(current_app, 'ga4_service', ga4_service)
                
                flash('GA4 credentials configured successfully', 'success')
                logger.info(f"GA4 credentials configured at {credentials_path}")
                
                # Redirect to admin dashboard
                return redirect(url_for('admin.index'))
            except json.JSONDecodeError:
                flash('Invalid JSON format. Please check your credentials JSON.', 'error')
                return render_template('admin/ga4_config.html', 
                                      credentials_exist=credentials_exist,
                                      existing_credentials=existing_credentials)
            except Exception as e:
                logger.error(f"Error configuring GA4 credentials: {e}")
                flash(f'Error configuring GA4 credentials: {str(e)}', 'error')
                return render_template('admin/ga4_config.html', 
                                      credentials_exist=credentials_exist,
                                      existing_credentials=existing_credentials)
        
        # Handle individual field input
        elif submission_method == 'fields':
            try:
                # Collect field values
                credentials = {
                    'type': request.form.get('type', 'service_account'),
                    'project_id': request.form.get('project_id', ''),
                    'private_key_id': request.form.get('private_key_id', ''),
                    'private_key': request.form.get('private_key', ''),
                    'client_email': request.form.get('client_email', ''),
                    'client_id': request.form.get('client_id', ''),
                    'auth_uri': request.form.get('auth_uri', 'https://accounts.google.com/o/oauth2/auth'),
                    'token_uri': request.form.get('token_uri', 'https://oauth2.googleapis.com/token'),
                    'auth_provider_x509_cert_url': request.form.get('auth_provider_x509_cert_url', 
                                                                   'https://www.googleapis.com/oauth2/v1/certs'),
                    'client_x509_cert_url': request.form.get('client_x509_cert_url', ''),
                    'universe_domain': request.form.get('universe_domain', 'googleapis.com')
                }
                
                # Validate required fields
                required_fields = ['project_id', 'private_key_id', 'private_key', 'client_email', 'client_id']
                missing_fields = [field for field in required_fields if not credentials[field]]
                
                if missing_fields:
                    flash(f'The following required fields are missing: {", ".join(missing_fields)}', 'error')
                    return render_template('admin/ga4_config.html', 
                                         credentials_exist=credentials_exist,
                                         existing_credentials=existing_credentials)
                
                # Create credentials directory if it doesn't exist
                credentials_dir = os.path.dirname(credentials_path)
                if not os.path.exists(credentials_dir):
                    os.makedirs(credentials_dir)
                
                # Write credentials to file
                with open(credentials_path, 'w') as f:
                    json.dump(credentials, f, indent=2)
                
                # Reinitialize GA4 service
                ga4_service = GA4Service(credentials_path=credentials_path)
                app_services = current_app.services if hasattr(current_app, 'services') else None
                if app_services:
                    app_services['ga4'] = ga4_service
                setattr(current_app, 'ga4_service', ga4_service)
                
                flash('GA4 credentials configured successfully', 'success')
                logger.info(f"GA4 credentials configured at {credentials_path}")
                
                # Redirect to admin dashboard
                return redirect(url_for('admin.index'))
                
            except Exception as e:
                logger.error(f"Error configuring GA4 credentials: {e}")
                flash(f'Error configuring GA4 credentials: {str(e)}', 'error')
        
        # Handle file upload
        elif submission_method == 'file':
            if 'credentials_file' not in request.files:
                flash('No file part in the request', 'error')
                return render_template('admin/ga4_config.html', 
                                     credentials_exist=credentials_exist,
                                     existing_credentials=existing_credentials)
                
            file = request.files['credentials_file']
            
            if file.filename == '':
                flash('No selected file', 'error')
                return render_template('admin/ga4_config.html', 
                                     credentials_exist=credentials_exist,
                                     existing_credentials=existing_credentials)
                
            try:
                # Read and validate file content
                file_content = file.read().decode('utf-8')
                json_data = json.loads(file_content)
                
                required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 
                                  'client_email', 'client_id', 'token_uri']
                missing_fields = [field for field in required_fields if field not in json_data]
                
                if missing_fields:
                    flash(f'The following required fields are missing from your credentials file: {", ".join(missing_fields)}', 'error')
                    return render_template('admin/ga4_config.html', 
                                         credentials_exist=credentials_exist,
                                         existing_credentials=existing_credentials)
                
                # Create credentials directory if it doesn't exist
                credentials_dir = os.path.dirname(credentials_path)
                if not os.path.exists(credentials_dir):
                    os.makedirs(credentials_dir)
                
                # Write credentials to file
                with open(credentials_path, 'w') as f:
                    f.write(file_content)
                
                # Reinitialize GA4 service
                ga4_service = GA4Service(credentials_path=credentials_path)
                app_services = current_app.services if hasattr(current_app, 'services') else None
                if app_services:
                    app_services['ga4'] = ga4_service
                setattr(current_app, 'ga4_service', ga4_service)
                
                flash('GA4 credentials configured successfully from uploaded file', 'success')
                logger.info(f"GA4 credentials configured at {credentials_path} from uploaded file")
                
                # Redirect to admin dashboard
                return redirect(url_for('admin.index'))
                
            except json.JSONDecodeError:
                flash('Invalid JSON format in uploaded file. Please check your credentials file.', 'error')
                return render_template('admin/ga4_config.html', 
                                     credentials_exist=credentials_exist,
                                     existing_credentials=existing_credentials)
            except Exception as e:
                logger.error(f"Error configuring GA4 credentials from file: {e}")
                flash(f'Error configuring GA4 credentials: {str(e)}', 'error')
                return render_template('admin/ga4_config.html', 
                                     credentials_exist=credentials_exist,
                                     existing_credentials=existing_credentials)
    
    # Display GA4 configuration form
    return render_template('admin/ga4_config.html', 
                         credentials_exist=credentials_exist,
                         existing_credentials=existing_credentials)

@admin_bp.route('/users')
@admin_required
def users():
    """User management."""
    # This is a placeholder for user management functionality
    return render_template('admin/users.html')

@admin_bp.route('/system-info')
@admin_required
def system_info():
    """Display system information."""
    info = {
        'python_version': os.environ.get('PYTHON_VERSION', 'Unknown'),
        'flask_version': os.environ.get('FLASK_VERSION', 'Unknown'),
        'database_path': current_app.config.get('DATABASE_PATH', 'Unknown'),
        'ga4_credentials': current_app.config.get('GA4_CREDENTIALS_PATH', 'Not configured'),
        'environment': current_app.config.get('ENV', 'development'),
    }
    
    return render_template('admin/system_info.html', info=info)