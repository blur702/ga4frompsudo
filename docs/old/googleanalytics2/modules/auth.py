import os
import json
import functools
from datetime import datetime, timedelta
from flask import session, redirect, url_for, request, current_app
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError

# OAuth 2.0 scopes for Google Analytics
SCOPES = [
    'https://www.googleapis.com/auth/analytics.readonly',
    'https://www.googleapis.com/auth/analytics'
]

def create_flow(redirect_uri=None):
    """
    Create an OAuth 2.0 flow object for Google authentication.
    
    Args:
        redirect_uri: The URI to redirect to after authorization.
        
    Returns:
        Flow: An OAuth 2.0 flow object or None if client ID is not configured.
    """
    # Check if client ID and secret are configured
    client_id = current_app.config['GOOGLE_CLIENT_ID']
    client_secret = current_app.config['GOOGLE_CLIENT_SECRET']
    
    if not client_id or not client_secret:
        current_app.logger.warning("Google OAuth credentials not configured. Using API key fallback if enabled.")
        return None
    
    client_config = {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "redirect_uris": [redirect_uri or url_for('oauth2callback', _external=True)]
        }
    }
    
    try:
        return Flow.from_client_config(
            client_config=client_config,
            scopes=SCOPES,
            redirect_uri=redirect_uri or url_for('oauth2callback', _external=True)
        )
    except Exception as e:
        current_app.logger.error(f"Error creating OAuth flow: {e}")
        return None

def build_credentials():
    """
    Build Google OAuth 2.0 credentials from the session.
    
    Returns:
        Credentials: Google OAuth 2.0 credentials or None if not available.
    """
    if 'credentials' not in session:
        return None
    
    credentials_info = json.loads(session['credentials'])
    
    credentials = Credentials(
        token=credentials_info.get('token'),
        refresh_token=credentials_info.get('refresh_token'),
        token_uri=credentials_info.get('token_uri'),
        client_id=credentials_info.get('client_id'),
        client_secret=credentials_info.get('client_secret'),
        scopes=credentials_info.get('scopes')
    )
    
    # Check if token is expired and refresh if necessary
    if credentials.expired:
        try:
            credentials.refresh(Request())
            # Update session with refreshed credentials
            save_credentials(credentials)
        except RefreshError:
            # If refresh fails, clear credentials and return None
            clear_credentials()
            return None
    
    return credentials

def save_credentials(credentials):
    """
    Save Google OAuth 2.0 credentials to the session.
    
    Args:
        credentials: Google OAuth 2.0 credentials.
    """
    session['credentials'] = json.dumps({
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes,
        'expiry': credentials.expiry.isoformat() if credentials.expiry else None
    })
    
    # Set session expiry to match token expiry
    if credentials.expiry:
        session.permanent = True
        current_app.permanent_session_lifetime = timedelta(seconds=(credentials.expiry - datetime.utcnow()).total_seconds())

def clear_credentials():
    """
    Clear Google OAuth 2.0 credentials from the session.
    """
    if 'credentials' in session:
        del session['credentials']

def is_logged_in():
    """
    Check if the user is logged in.
    
    Returns:
        bool: True if the user is logged in, False otherwise.
    """
    try:
        # Check if OAuth credentials are available
        oauth_logged_in = 'credentials' in session and build_credentials() is not None
        
        # If OAuth fallback is enabled and API key is configured, consider the user logged in
        if not oauth_logged_in and current_app.config.get('OAUTH_FALLBACK_ENABLED', False):
            try:
                from modules.models import Setting
                api_key = Setting.get_value('google_api_key')
                if api_key:
                    current_app.logger.info("Using API key fallback for authentication")
                    return True
            except Exception as e:
                current_app.logger.error(f"Error checking API key: {e}")
                # Don't fail if there's an error checking the API key
                pass
        
        return oauth_logged_in
    except Exception as e:
        current_app.logger.error(f"Error in is_logged_in: {e}")
        return False

def login_required(f):
    """
    Decorator to require login for a route.
    
    Args:
        f: The function to decorate.
        
    Returns:
        function: The decorated function.
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_logged_in():
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def get_user_info():
    """
    Get information about the authenticated user.
    
    Returns:
        dict: User information or None if not available.
    """
    credentials = build_credentials()
    if not credentials:
        return None
    
    try:
        service = build('oauth2', 'v2', credentials=credentials)
        user_info = service.userinfo().get().execute()
        return user_info
    except Exception as e:
        current_app.logger.error(f"Error getting user info: {e}")
        return None

def revoke_token():
    """
    Revoke the current OAuth 2.0 token.
    
    Returns:
        bool: True if successful, False otherwise.
    """
    credentials = build_credentials()
    if not credentials:
        return False
    
    try:
        credentials.revoke(Request())
        clear_credentials()
        return True
    except Exception as e:
        current_app.logger.error(f"Error revoking token: {e}")
        return False