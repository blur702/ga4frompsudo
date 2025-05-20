"""
Admin controller for handling admin-specific functionality.
"""

import os
import json
import logging
import secrets
from typing import Dict, Any, Optional
from flask import Blueprint, request, redirect, url_for, flash, render_template, current_app, jsonify, session

from app.controllers.auth_controller import admin_required
from app.services import get_service
from app.services.ga4_service import GA4Service
from app.models.app_settings import AppSettings
from app.models.property import Property
from app.models.website import Website
from app.models.user import User

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
    
    # Get current authentication method from settings
    db = current_app.database
    current_auth_method = AppSettings.get_setting(db, 'ga4_auth_method', 'service_account')
    
    # Get OAuth2 settings from config and database
    oauth_config = current_app.config.get('AUTH', {})
    # Check database for OAuth2 settings
    client_id = AppSettings.get_setting(db, 'oauth2_client_id')
    client_secret = AppSettings.get_setting(db, 'oauth2_client_secret')
    access_token = AppSettings.get_setting(db, 'oauth2_access_token')
    refresh_token = AppSettings.get_setting(db, 'oauth2_refresh_token')
    
    # OAuth is configured if we have client ID and secret
    oauth_configured = bool(client_id and client_secret)
    
    # Update oauth_config with database values
    if client_id:
        oauth_config['client_id'] = client_id
    if client_secret:
        oauth_config['client_secret'] = client_secret
    
    # Check if we have tokens (fully authorized)
    oauth_config['has_tokens'] = bool(access_token and refresh_token)
    
    # Handle form submission
    if request.method == 'POST':
        auth_method = request.form.get('auth_method', 'service_account')
        submission_method = request.form.get('submission_method', '')
        
        # Save the authentication method
        AppSettings.set_setting(
            db, 
            'ga4_auth_method', 
            auth_method,
            'Authentication method for GA4 API (service_account or oauth2)'
        )
        
        if auth_method == 'service_account':
            # Handle service account credential upload
            if submission_method == 'json':
                credentials_json = request.form.get('credentials_json', '').strip()
                if not credentials_json:
                    flash('GA4 credentials JSON is required', 'error')
                    return render_template('admin/ga4_config.html', 
                                          credentials_exist=credentials_exist,
                                          existing_credentials=existing_credentials,
                                          current_auth_method=current_auth_method,
                                          oauth_configured=oauth_configured,
                                          oauth_config=oauth_config)
                
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
                                              existing_credentials=existing_credentials,
                                              current_auth_method=current_auth_method,
                                              oauth_configured=oauth_configured,
                                          oauth_config=oauth_config)
                    
                    # Create credentials directory if it doesn't exist
                    credentials_dir = os.path.dirname(credentials_path)
                    if not os.path.exists(credentials_dir):
                        os.makedirs(credentials_dir)
                    
                    # Write credentials to file
                    with open(credentials_path, 'w') as f:
                        f.write(credentials_json)
                    
                    # Reinitialize GA4 service with service account
                    ga4_service = GA4Service(credentials_path=credentials_path, auth_method='service_account')
                    app_services = current_app.services if hasattr(current_app, 'services') else None
                    if app_services:
                        app_services['ga4'] = ga4_service
                    setattr(current_app, 'ga4_service', ga4_service)
                    
                    flash('GA4 service account credentials configured successfully', 'success')
                    logger.info(f"GA4 credentials configured at {credentials_path}")
                    
                    # Redirect to admin dashboard
                    return redirect(url_for('admin.index'))
                except json.JSONDecodeError:
                    flash('Invalid JSON format. Please check your credentials JSON.', 'error')
                    return render_template('admin/ga4_config.html', 
                                          credentials_exist=credentials_exist,
                                          existing_credentials=existing_credentials,
                                          current_auth_method=current_auth_method,
                                          oauth_configured=oauth_configured,
                                          oauth_config=oauth_config)
                except Exception as e:
                    logger.error(f"Error configuring GA4 credentials: {e}")
                    flash(f'Error configuring GA4 credentials: {str(e)}', 'error')
                    return render_template('admin/ga4_config.html', 
                                          credentials_exist=credentials_exist,
                                          existing_credentials=existing_credentials,
                                          current_auth_method=current_auth_method,
                                          oauth_configured=oauth_configured,
                                          oauth_config=oauth_config)
            
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
                                             existing_credentials=existing_credentials,
                                             current_auth_method=current_auth_method,
                                             oauth_configured=oauth_configured,
                                          oauth_config=oauth_config)
                    
                    # Create credentials directory if it doesn't exist
                    credentials_dir = os.path.dirname(credentials_path)
                    if not os.path.exists(credentials_dir):
                        os.makedirs(credentials_dir)
                    
                    # Write credentials to file
                    with open(credentials_path, 'w') as f:
                        json.dump(credentials, f, indent=2)
                    
                    # Reinitialize GA4 service
                    ga4_service = GA4Service(credentials_path=credentials_path, auth_method='service_account')
                    app_services = current_app.services if hasattr(current_app, 'services') else None
                    if app_services:
                        app_services['ga4'] = ga4_service
                    setattr(current_app, 'ga4_service', ga4_service)
                    
                    flash('GA4 service account credentials configured successfully', 'success')
                    logger.info(f"GA4 credentials configured at {credentials_path}")
                    
                    # Redirect to admin dashboard
                    return redirect(url_for('admin.index'))
                except Exception as e:
                    logger.error(f"Error configuring GA4 credentials: {e}")
                    flash(f'Error configuring GA4 credentials: {str(e)}', 'error')
                    return render_template('admin/ga4_config.html', 
                                         credentials_exist=credentials_exist,
                                         existing_credentials=existing_credentials,
                                         current_auth_method=current_auth_method,
                                         oauth_configured=oauth_configured,
                                          oauth_config=oauth_config)
        
        elif auth_method == 'oauth2':
            # Handle OAuth2 configuration
            if submission_method == 'oauth_config':
                try:
                    client_id = request.form.get('oauth_client_id', '').strip()
                    client_secret = request.form.get('oauth_client_secret', '').strip()
                    
                    if not client_id or not client_secret:
                        flash('OAuth2 Client ID and Client Secret are required', 'error')
                        return render_template('admin/ga4_config.html', 
                                              credentials_exist=credentials_exist,
                                              existing_credentials=existing_credentials,
                                              current_auth_method=current_auth_method,
                                              oauth_configured=oauth_configured,
                                          oauth_config=oauth_config)
                    
                    # Save OAuth2 configuration to settings
                    AppSettings.set_setting(db, 'oauth2_client_id', client_id, 'OAuth2 Client ID for GA4')
                    AppSettings.set_setting(db, 'oauth2_client_secret', client_secret, 'OAuth2 Client Secret for GA4')
                    
                    # Don't reinitialize GA4 service yet - we need tokens first
                    flash('OAuth2 configuration saved successfully. Click "Authorize with Google" to complete setup.', 'success')
                    
                    # Redirect back to the config page so user can click authorize
                    return redirect(url_for('admin.ga4_config'))
                    
                except Exception as e:
                    logger.error(f"Error configuring OAuth2: {e}")
                    flash(f'Error configuring OAuth2: {str(e)}', 'error')
                    return render_template('admin/ga4_config.html', 
                                          credentials_exist=credentials_exist,
                                          existing_credentials=existing_credentials,
                                          current_auth_method=current_auth_method,
                                          oauth_configured=oauth_configured,
                                          oauth_config=oauth_config)
    
    # GET request - display form
    return render_template('admin/ga4_config.html', 
                          credentials_exist=credentials_exist,
                          existing_credentials=existing_credentials,
                          current_auth_method=current_auth_method,
                          oauth_configured=oauth_configured,
                          oauth_config=oauth_config)

@admin_bp.route('/ga4-authorize-oauth')
@admin_required
def ga4_authorize_oauth():
    """Initiate OAuth2 authorization flow."""
    try:
        # Build and redirect to OAuth2 authorization URL
        auth_url = _build_oauth2_auth_url()
        return redirect(auth_url)
    except Exception as e:
        logger.error(f"Error initiating OAuth2 flow: {e}")
        flash(f'Error initiating OAuth2 authorization: {str(e)}', 'error')
        return redirect(url_for('admin.ga4_config'))

@admin_bp.route('/ga4-oauth-callback')
@admin_required
def ga4_oauth_callback():
    """Handle OAuth2 callback from Google."""
    code = request.args.get('code')
    state = request.args.get('state')
    
    if not code:
        flash('OAuth2 authorization failed: No authorization code received', 'error')
        return redirect(url_for('admin.ga4_config'))
    
    # Verify state for security
    stored_state = session.get('oauth2_state')
    if not stored_state or stored_state != state:
        flash('OAuth2 authorization failed: Invalid state parameter', 'error')
        return redirect(url_for('admin.ga4_config'))
    
    try:
        # Exchange code for tokens
        token_data = _exchange_oauth2_code(code)
        
        if not token_data:
            flash('Failed to exchange authorization code for tokens', 'error')
            return redirect(url_for('admin.ga4_config'))
        
        # Store tokens securely in database
        db = current_app.database
        AppSettings.set_setting(db, 'oauth2_access_token', token_data.get('access_token'), 'OAuth2 Access Token')
        AppSettings.set_setting(db, 'oauth2_refresh_token', token_data.get('refresh_token'), 'OAuth2 Refresh Token')
        AppSettings.set_setting(db, 'oauth2_token_expiry', str(token_data.get('expires_in', 3600)), 'OAuth2 Token Expiry')
        
        # Initialize GA4 service with OAuth2 credentials
        try:
            ga4_service = GA4Service(auth_method='oauth2')
            
            # Update the application's GA4 service
            app_services = current_app.services if hasattr(current_app, 'services') else None
            if app_services:
                app_services['ga4'] = ga4_service
            setattr(current_app, 'ga4_service', ga4_service)
            
            logger.info("Successfully initialized GA4 service with OAuth2 credentials")
        except Exception as e:
            logger.error(f"Error initializing GA4 service with OAuth2: {e}")
            # Continue anyway - the tokens are saved
        
        flash('OAuth2 authorization successful', 'success')
        return redirect(url_for('admin.index'))
        
    except Exception as e:
        logger.error(f"OAuth2 callback error: {e}")
        flash(f'OAuth2 authorization failed: {str(e)}', 'error')
        return redirect(url_for('admin.ga4_config'))

@admin_bp.route('/system-info')
@admin_required
def system_info():
    """Display system information and application status."""
    ga4_service = get_service('ga4')
    
    system_data = {
        'ga4_service_available': ga4_service.is_available() if ga4_service else False,
        'database_path': current_app.config.get('DATABASE_PATH'),
        'credentials_path': current_app.config.get('GA4_CREDENTIALS_PATH'),
        'app_name': current_app.config.get('APP_NAME'),
        'environment': current_app.config.get('ENV', 'production'),
        'debug_mode': current_app.debug,
    }
    
    return render_template('admin/system_info.html', system_data=system_data)

@admin_bp.route('/test-ga4-connection')
@admin_required
def test_ga4_connection():
    """Test the GA4 API connection and return status."""
    ga4_service = get_service('ga4')
    
    if not ga4_service:
        return jsonify({
            'success': False,
            'error': 'GA4 service not initialized'
        })
    
    try:
        # Try to list account summaries as a connection test
        account_summaries = ga4_service.list_account_summaries()
        
        return jsonify({
            'success': True,
            'message': f'Successfully connected to GA4 API. Found {len(account_summaries)} account(s).',
            'accounts': len(account_summaries),
            'service_available': ga4_service.is_available()
        })
    except Exception as e:
        logger.error(f"GA4 connection test failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'service_available': ga4_service.is_available()
        })

@admin_bp.route('/users')
@admin_required
def users():
    """User management page."""
    # Get all users from database
    users = User.find_all(current_app.database)
    
    # Get current user for the template
    auth_service = get_service('auth')
    current_user = auth_service.get_current_user() if auth_service else None
    
    return render_template('admin/users.html', users=users, current_user=current_user)

@admin_bp.route('/properties')
@admin_required
def properties():
    """Display and manage GA4 properties."""
    try:
        # Get all properties from database
        properties = Property.find_all(current_app.database, order_by="property_name ASC")
        
        # Add website information to each property
        for prop in properties:
            prop.websites = prop.get_websites()
        
        # Get sync service for summary
        sync_service = get_service('property_sync')
        summary = sync_service.get_sync_summary() if sync_service else {'total_properties': len(properties), 'total_websites': 0}
        
        return render_template('admin/properties.html', 
                             properties=properties,
                             summary=summary)
    except Exception as e:
        logger.error(f"Error displaying properties: {e}")
        flash(f'Error loading properties: {str(e)}', 'error')
        return redirect(url_for('admin.index'))

@admin_bp.route('/sync-properties', methods=['POST'])
@admin_required
def sync_properties():
    """Sync all GA4 properties with the local database."""
    sync_service = get_service('property_sync')
    
    if not sync_service:
        return jsonify({
            'success': False,
            'message': 'Property sync service is not available. Please configure GA4 credentials.'
        })
    
    try:
        results = sync_service.sync_all_properties(fetch_websites=True, update_existing=True)
        
        message = f"Synced {results['properties_created']} new properties and {results['websites_created']} new websites"
        
        if results['properties_updated'] > 0:
            message += f", updated {results['properties_updated']} properties"
            
        if results['errors']:
            message += f". {len(results['errors'])} errors occurred."
            
        return jsonify({
            'success': True,
            'message': message,
            'results': results
        })
    except Exception as e:
        logger.error(f"Error syncing properties: {e}")
        return jsonify({
            'success': False,
            'message': f'Error syncing properties: {str(e)}'
        })

def _build_oauth2_auth_url() -> str:
    """Build the OAuth2 authorization URL for Google Analytics."""
    import urllib.parse
    
    base_url = "https://accounts.google.com/o/oauth2/v2/auth"
    
    # Get OAuth2 settings from database
    db = current_app.database
    client_id = AppSettings.get_setting(db, 'oauth2_client_id')
    
    # Use the configured redirect URI or build one
    redirect_uri = request.url_root.rstrip('/') + url_for('admin.ga4_oauth_callback')
    
    # Store state for security
    state = secrets.token_urlsafe(32)
    session['oauth2_state'] = state
    
    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': ' '.join([
            'https://www.googleapis.com/auth/analytics.readonly',
            'https://www.googleapis.com/auth/analytics',
            'https://www.googleapis.com/auth/analytics.manage.users',
            'https://www.googleapis.com/auth/analytics.manage.users.readonly'
        ]),
        'access_type': 'offline',
        'state': state,
        'prompt': 'consent'  # Force consent to get refresh token
    }
    
    return f"{base_url}?{urllib.parse.urlencode(params)}"

def _exchange_oauth2_code(code: str) -> Optional[Dict[str, Any]]:
    """Exchange OAuth2 authorization code for access tokens."""
    try:
        import requests
    except ImportError:
        logger.error("requests module not available")
        return None
    
    token_url = "https://oauth2.googleapis.com/token"
    
    # Get OAuth2 settings from database
    db = current_app.database
    client_id = AppSettings.get_setting(db, 'oauth2_client_id')
    client_secret = AppSettings.get_setting(db, 'oauth2_client_secret')
    redirect_uri = request.url_root.rstrip('/') + url_for('admin.ga4_oauth_callback')
    
    data = {
        'code': code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    }
    
    try:
        response = requests.post(token_url, data=data)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error exchanging OAuth2 code: {e}")
        return None

@admin_bp.route('/api/users', methods=['POST'])
@admin_required
def api_create_user():
    """API endpoint to create a new user."""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'password', 'first_name', 'last_name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Check if user already exists
        existing_user = User.find_by_email(current_app.database, data['email'])
        if existing_user:
            return jsonify({'error': 'User with this email already exists'}), 400
        
        # Get services
        security_service = get_service('security')
        
        # Hash the password
        password_hash, salt = security_service.hash_password(data['password'])
        # Store as hash:salt format
        combined_hash = f"{password_hash}:{salt}"
        
        # Create user
        user = User(
            database=current_app.database,
            email=data['email'],
            password_hash=combined_hash,
            first_name=data['first_name'],
            last_name=data['last_name'],
            roles=data.get('roles', ['user']),
            is_active=data.get('is_active', True)
        )
        
        user_id = user.save()
        
        if user_id:
            logger.info(f"Created new user: {data['email']}")
            return jsonify({'success': True, 'user_id': user_id}), 201
        else:
            return jsonify({'error': 'Failed to create user'}), 500
            
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/users/<int:user_id>', methods=['GET'])
@admin_required
def api_get_user(user_id):
    """API endpoint to get a specific user."""
    try:
        user = User.find_by_id(current_app.database, user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        return jsonify(user.to_dict(exclude_sensitive=True))
        
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/users/<int:user_id>', methods=['PUT'])
@admin_required
def api_update_user(user_id):
    """API endpoint to update a user."""
    try:
        data = request.get_json()
        
        user = User.find_by_id(current_app.database, user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Update fields
        if 'email' in data:
            user.email = data['email']
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'roles' in data:
            user.roles = data['roles']
        if 'is_active' in data:
            user.is_active = data['is_active']
        
        # Save changes
        if user.save():
            logger.info(f"Updated user: {user.email}")
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Failed to update user'}), 500
            
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/users/<int:user_id>/reset-password', methods=['POST'])
@admin_required
def api_reset_password(user_id):
    """API endpoint to reset a user's password."""
    try:
        data = request.get_json()
        
        if not data.get('password'):
            return jsonify({'error': 'Password is required'}), 400
        
        user = User.find_by_id(current_app.database, user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get security service
        security_service = get_service('security')
        
        # Hash the new password
        password_hash, salt = security_service.hash_password(data['password'])
        # Store as hash:salt format
        user.password_hash = f"{password_hash}:{salt}"
        
        # Save changes
        if user.save():
            logger.info(f"Reset password for user: {user.email}")
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Failed to reset password'}), 500
            
    except Exception as e:
        logger.error(f"Error resetting password for user {user_id}: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/users/<int:user_id>', methods=['DELETE'])
@admin_required
def api_delete_user(user_id):
    """API endpoint to delete a user."""
    try:
        # Prevent deleting current user
        auth_service = get_service('auth')
        current_user = auth_service.get_current_user()
        
        if current_user and current_user.id == user_id:
            return jsonify({'error': 'Cannot delete current user'}), 400
        
        user = User.find_by_id(current_app.database, user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if user.delete():
            logger.info(f"Deleted user: {user.email}")
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Failed to delete user'}), 500
            
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/sync-property/<property_id>', methods=['POST'])
@admin_required
def sync_single_property(property_id):
    """Sync a single GA4 property with the local database."""
    sync_service = get_service('property_sync')
    
    if not sync_service:
        return jsonify({
            'success': False,
            'message': 'Property sync service is not available. Please configure GA4 credentials.'
        })
    
    try:
        results = sync_service.sync_single_property(
            property_id=property_id,
            fetch_websites=True,
            update_existing=True
        )
        
        message = f"Property synced successfully"
        
        if results['websites_created'] > 0:
            message += f", added {results['websites_created']} websites"
            
        if results['errors']:
            message += f". {len(results['errors'])} errors occurred."
            
        return jsonify({
            'success': True,
            'message': message,
            'results': results
        })
    except Exception as e:
        logger.error(f"Error syncing property {property_id}: {e}")
        return jsonify({
            'success': False,
            'message': f'Error syncing property: {str(e)}'
        })