"""
Authentication controller for handling user login, logout, and account management.
"""

import logging
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
    
    GET: Display the login form
    POST: Process the login form submission
    """
    # Handle form submission
    if request.method == 'POST':
        email = request.form.get('email', '')
        password = request.form.get('password', '')
        
        # Validate inputs
        if not email or not password:
            flash('Email and password are required', 'error')
            return render_template('auth/login.html')
            
        if not is_valid_email(email):
            flash('Invalid email format', 'error')
            return render_template('auth/login.html')
        
        # Get auth service
        auth_service = get_service('auth')
        if not auth_service:
            logger.error("Auth service not available")
            flash('Authentication service is unavailable', 'error')
            return render_template('auth/login.html')
        
        # Attempt login
        success, user, error_msg = auth_service.login(email, password)
        
        if success and user:
            # Record successful login
            auth_service.record_login_attempt(email, True)
            
            # Get redirect target (default to dashboard)
            next_url = request.args.get('next', url_for('dashboard.index'))
            
            # Redirect to the dashboard or requested page
            return redirect(next_url)
        else:
            # Record failed login
            auth_service.record_login_attempt(email, False)
            
            # Show error message
            flash(error_msg or 'Invalid login credentials', 'error')
            return render_template('auth/login.html')
    
    # Display login form for GET requests
    return render_template('auth/login.html')

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
    Redirects to login page if user is not logged in.
    """
    def wrapped_view(*args, **kwargs):
        auth_service = get_service('auth')
        if not auth_service:
            logger.error("Auth service not available for login_required check")
            flash('Authentication service is unavailable', 'error')
            return redirect(url_for('auth.login', next=request.path))
        
        user = auth_service.require_login()
        if not user:
            flash('Please log in to access this page', 'warning')
            return redirect(url_for('auth.login', next=request.path))
            
        return view_func(*args, **kwargs)
    
    # Preserve function name and docstring
    wrapped_view.__name__ = view_func.__name__
    wrapped_view.__doc__ = view_func.__doc__
    
    return wrapped_view

def admin_required(view_func):
    """
    Decorator to protect routes that require admin privileges.
    Redirects to dashboard if user is not an admin.
    """
    def wrapped_view(*args, **kwargs):
        auth_service = get_service('auth')
        if not auth_service:
            logger.error("Auth service not available for admin_required check")
            flash('Authentication service is unavailable', 'error')
            return redirect(url_for('auth.login', next=request.path))
        
        user = auth_service.require_role('admin')
        if not user:
            flash('You do not have permission to access this page', 'error')
            return redirect(url_for('dashboard.index'))
            
        return view_func(*args, **kwargs)
    
    # Preserve function name and docstring
    wrapped_view.__name__ = view_func.__name__
    wrapped_view.__doc__ = view_func.__doc__
    
    return wrapped_view