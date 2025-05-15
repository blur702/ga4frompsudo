import logging
import secrets
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple, List

from flask import current_app, session, request

from app.models.user import User
from app.services.security_service import SecurityService

logger = logging.getLogger(__name__)

class AuthService:
    """
    Service for managing user authentication, sessions, and permissions.
    
    This service handles:
    - User login and session management
    - Token generation and validation
    - Permission checking based on user roles
    - Session renewal and timeout management
    """
    def __init__(self, security_service: SecurityService):
        self.security_service = security_service
        self.session_duration = current_app.config.get('SESSION_DURATION', 3600)  # Default: 1 hour
        self.token_expiry = current_app.config.get('TOKEN_EXPIRY', 86400)  # Default: 24 hours

    def login(self, email: str, password: str) -> Tuple[bool, Optional[User], Optional[str]]:
        """
        Authenticate a user by email and password.
        
        Args:
            email: User's email address
            password: User's password
            
        Returns:
            Tuple containing:
            - Success status (bool)
            - User object if successful, None otherwise
            - Error message if unsuccessful, None otherwise
        """
        logger.debug(f"Login attempt for email: {email}")
        
        # Find user by email
        user = User.find_by_email(email)
        if not user:
            logger.warning(f"Login failed: No user found with email {email}")
            return False, None, "Invalid email or password"
        
        # Check if user is active
        if not user.is_active:
            logger.warning(f"Login failed: User {email} is inactive")
            return False, None, "Account is inactive. Please contact an administrator."
        
        # Verify password
        if not self.security_service.verify_password(password, user.password_hash):
            logger.warning(f"Login failed: Invalid password for {email}")
            return False, None, "Invalid email or password"
        
        # Create session
        self._create_session(user)
        
        logger.info(f"User {email} logged in successfully")
        return True, user, None

    def logout(self) -> None:
        """Clear the current user session."""
        session.clear()
        logger.info("User logged out successfully")

    def get_current_user(self) -> Optional[User]:
        """
        Get the currently logged-in user from the session.
        
        Returns:
            User object if logged in, None otherwise
        """
        user_id = session.get('user_id')
        if not user_id:
            return None
            
        # Check if session has expired
        last_active = session.get('last_active', 0)
        current_time = int(time.time())
        
        if current_time - last_active > self.session_duration:
            logger.info(f"Session expired for user_id {user_id}")
            session.clear()
            return None
            
        # Update last active time
        session['last_active'] = current_time
        
        return User.find_by_id(user_id)

    def require_login(self) -> Optional[User]:
        """
        Check if a user is logged in. Intended to be used as a route guard.
        
        Returns:
            User object if logged in, None otherwise
        """
        return self.get_current_user()

    def require_role(self, role: str) -> Optional[User]:
        """
        Check if the current user has the specified role.
        
        Args:
            role: Role name to check for ('admin', 'user', etc.)
            
        Returns:
            User object if user has the role, None otherwise
        """
        user = self.get_current_user()
        if not user:
            logger.debug(f"Role check failed: No user logged in")
            return None
            
        if role not in user.roles:
            logger.warning(f"Role check failed: User {user.email} does not have role '{role}'")
            return None
            
        return user

    def generate_api_token(self, user_id: int, scopes: List[str] = None) -> str:
        """
        Generate an API token for a user with specified permission scopes.
        
        Args:
            user_id: ID of the user to generate token for
            scopes: List of permission scopes for this token
            
        Returns:
            Encoded API token
        """
        if scopes is None:
            scopes = ['read']
            
        # Create token payload
        now = int(time.time())
        payload = {
            'sub': user_id,
            'iat': now,
            'exp': now + self.token_expiry,
            'scopes': scopes
        }
        
        # Generate and return token
        token = self.security_service.generate_token(payload)
        logger.info(f"Generated API token for user_id {user_id} with scopes {scopes}")
        
        return token

    def validate_api_token(self, token: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Validate an API token and extract its payload.
        
        Args:
            token: The token to validate
            
        Returns:
            Tuple containing:
            - Success status (bool)
            - Token payload if successful, None otherwise
        """
        try:
            payload = self.security_service.decode_token(token)
            
            # Check if token has expired
            current_time = int(time.time())
            if payload.get('exp', 0) < current_time:
                logger.warning(f"API token validation failed: Token expired")
                return False, None
                
            logger.debug(f"API token validated successfully for user_id {payload.get('sub')}")
            return True, payload
        except Exception as e:
            logger.warning(f"API token validation failed: {str(e)}")
            return False, None

    def check_token_scope(self, payload: Dict[str, Any], required_scope: str) -> bool:
        """
        Check if a token payload contains the required scope.
        
        Args:
            payload: Token payload (from validate_api_token)
            required_scope: The scope to check for
            
        Returns:
            True if token has the required scope, False otherwise
        """
        scopes = payload.get('scopes', [])
        if required_scope in scopes or 'admin' in scopes:
            return True
            
        logger.warning(f"Token scope check failed: {required_scope} not in {scopes}")
        return False

    def _create_session(self, user: User) -> None:
        """
        Create a new session for the authenticated user.
        
        Args:
            user: The authenticated user object
        """
        # Set session data
        session.clear()
        session['user_id'] = user.id
        session['last_active'] = int(time.time())
        
        # Set session cookie options from config
        session.permanent = True
        current_app.permanent_session_lifetime = timedelta(seconds=self.session_duration)
        
        # Generate CSRF token for additional security
        session['csrf_token'] = secrets.token_hex(16)
        
        logger.debug(f"Created new session for user_id {user.id}")

    def check_csrf_token(self, token: str) -> bool:
        """
        Validate a CSRF token against the one stored in the session.
        
        Args:
            token: The CSRF token to validate
            
        Returns:
            True if token is valid, False otherwise
        """
        session_token = session.get('csrf_token')
        if not session_token or session_token != token:
            logger.warning(f"CSRF token validation failed")
            return False
            
        return True

    def get_client_ip(self) -> str:
        """
        Get the client's IP address from the request.
        
        Returns:
            IP address as a string
        """
        # Try to get IP from X-Forwarded-For header first (when behind a proxy)
        if request.headers.get('X-Forwarded-For'):
            ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
        else:
            ip = request.remote_addr or 'unknown'
            
        return ip

    def record_login_attempt(self, email: str, success: bool) -> None:
        """
        Record a login attempt for security monitoring.
        
        Args:
            email: The email used in the login attempt
            success: Whether the attempt was successful
        """
        ip_address = self.get_client_ip()
        timestamp = datetime.utcnow()
        
        # In a real implementation, this would typically record to a database table
        # For now, we'll just log it
        if success:
            logger.info(f"Successful login for {email} from {ip_address} at {timestamp}")
        else:
            logger.warning(f"Failed login attempt for {email} from {ip_address} at {timestamp}")