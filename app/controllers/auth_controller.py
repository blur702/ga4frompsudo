"""
Authentication controller for handling user login, logout, and account management.
"""

import logging
import time
from flask import Blueprint, request, redirect, url_for, flash, render_template, session, current_app

from app.services import get_service
from app.utils.security_utils import is_valid_email, is_valid_password

logger = logging.getLogger(__name__)

# Create blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handle user login.
    
    DEVELOPMENT BYPASS: Automatically logs in as admin and redirects to admin dashboard
    """
    # DEVELOPMENT BYPASS: Automatically log in as admin
    logger.warning("DEVELOPMENT MODE: Login bypassed, automatically logging in as admin")
    
    # Set admin session
    session['user_id'] = 2  # ID of the admin user kevin.althaus@mail.house.gov
    session['user_roles'] = ['admin']
    session['last_active'] = int(time.time())
    
    # Get redirect target (default to admin dashboard)
    next_url = request.args.get('next', url_for('admin.index'))
    
    # Redirect directly to admin dashboard
    return redirect(next_url)

@auth_bp.route('/logout')
def logout():
    """
    Handle user logout by clearing the session.
    """
    # Get auth service
    auth_service = get_service('auth')
    if auth_service:
        auth_service.logout()
    else:
        # Fallback if service unavailable
        session.clear()
    
    flash('You have been logged out', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Handle user registration.
    
    GET: Display the registration form
    POST: Process the registration form submission
    """
    # This route is a placeholder for user registration
    # In the initial implementation, we'll display a message
    # that user accounts are managed by administrators
    
    flash('User registration is currently handled by administrators. Please contact an admin to create an account.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """
    Handle password reset requests.
    
    GET: Display the password reset request form
    POST: Process the password reset request
    """
    # This route is a placeholder for password reset functionality
    
    flash('Password reset functionality is currently handled by administrators. Please contact an admin for assistance.', 'info')
    return redirect(url_for('auth.login'))

# Auth middleware for route protection
def login_required(view_func):
    """
    Decorator to protect routes that require authentication.
    CURRENTLY BYPASSED FOR DEVELOPMENT - all routes are accessible without login.
    """
    def wrapped_view(*args, **kwargs):
        # BYPASS: Automatically create a session for development
        if 'user_id' not in session:
            # Set session variables for an admin user
            session['user_id'] = 2  # ID of the admin user kevin.althaus@mail.house.gov
            session['user_roles'] = ['admin']
            session['last_active'] = int(time.time())
            logger.warning("DEVELOPMENT MODE: Authentication bypassed, using admin session")
        
        # Always allow access
        return view_func(*args, **kwargs)
    
    # Preserve function name and docstring
    wrapped_view.__name__ = view_func.__name__
    wrapped_view.__doc__ = view_func.__doc__
    
    return wrapped_view

def admin_required(view_func):
    """
    Decorator to protect routes that require admin privileges.
    CURRENTLY BYPASSED FOR DEVELOPMENT - all routes are accessible.
    """
    def wrapped_view(*args, **kwargs):
        # BYPASS: Automatically create a session for development with admin role
        if 'user_id' not in session:
            # Set session variables for an admin user
            session['user_id'] = 2  # ID of the admin user kevin.althaus@mail.house.gov
            session['user_roles'] = ['admin']
            session['last_active'] = int(time.time())
            logger.warning("DEVELOPMENT MODE: Admin authentication bypassed, using admin session")
        elif 'admin' not in session.get('user_roles', []):
            # If there's a session but no admin role, add it
            session['user_roles'] = ['admin'] 
            logger.warning("DEVELOPMENT MODE: Admin role automatically added to session")
        
        # Always allow access
        return view_func(*args, **kwargs)
    
    # Preserve function name and docstring
    wrapped_view.__name__ = view_func.__name__
    wrapped_view.__doc__ = view_func.__doc__
    
    return wrapped_view