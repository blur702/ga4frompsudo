import os
import time
import unittest
from unittest.mock import patch, MagicMock

from flask import Flask

from app.services.security_service import SecurityService
from app.services.auth_service import AuthService
from app.models.user import User
from app.models.database import Database


class TestAuthService(unittest.TestCase):
    """Test suite for the AuthService class."""

    def setUp(self):
        """Set up the test environment before each test."""
        # Create a test Flask app
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.app.config['SESSION_DURATION'] = 3600
        self.app.config['TOKEN_EXPIRY'] = 86400
        
        # Create a mock database
        self.mock_db = MagicMock(spec=Database)
        
        # Create a test security service
        self.security_service = SecurityService(
            key_file_path=None,  # No file for testing
            salt='test_salt'
        )
        
        # Create and patch a mock user
        self.mock_user = MagicMock(spec=User)
        self.mock_user.id = 1
        self.mock_user.email = 'test@example.com'
        self.mock_user.password_hash = self.security_service.hash_password('password123')
        self.mock_user.is_active = True
        self.mock_user.roles = ['user']
        
        # Create the auth service
        with self.app.app_context():
            self.auth_service = AuthService(self.security_service, self.mock_db)

    @patch('app.models.user.User.find_by_email')
    def test_login_success(self, mock_find_by_email):
        """Test successful login with valid credentials."""
        # Configure the mock
        mock_find_by_email.return_value = self.mock_user
        
        # Test login with valid credentials
        with self.app.test_request_context():
            with self.app.test_client() as client:
                with client.session_transaction() as session:
                    success, user, error = self.auth_service.login('test@example.com', 'password123')
                    
                    self.assertTrue(success)
                    self.assertEqual(user, self.mock_user)
                    self.assertIsNone(error)
                    self.assertIn('user_id', session)
                    self.assertEqual(session['user_id'], 1)
                    
                    # Verify that find_by_email was called with the database and email
                    mock_find_by_email.assert_called_once_with(self.mock_db, 'test@example.com')

    @patch('app.models.user.User.find_by_email')
    def test_login_invalid_email(self, mock_find_by_email):
        """Test login with non-existent email."""
        # Configure the mock to return None (user not found)
        mock_find_by_email.return_value = None
        
        # Test login with invalid email
        with self.app.test_request_context():
            success, user, error = self.auth_service.login('nonexistent@example.com', 'password123')
            
            self.assertFalse(success)
            self.assertIsNone(user)
            self.assertEqual(error, "Invalid email or password")
            
            # Verify that find_by_email was called with the database and email
            mock_find_by_email.assert_called_once_with(self.mock_db, 'nonexistent@example.com')

    @patch('app.models.user.User.find_by_email')
    def test_login_invalid_password(self, mock_find_by_email):
        """Test login with invalid password."""
        # Configure the mock
        mock_find_by_email.return_value = self.mock_user
        
        # Test login with invalid password
        with self.app.test_request_context():
            success, user, error = self.auth_service.login('test@example.com', 'wrongpassword')
            
            self.assertFalse(success)
            self.assertIsNone(user)
            self.assertEqual(error, "Invalid email or password")

    @patch('app.models.user.User.find_by_email')
    def test_login_inactive_user(self, mock_find_by_email):
        """Test login with inactive user account."""
        # Configure the mock with an inactive user
        inactive_user = MagicMock(spec=User)
        inactive_user.email = 'inactive@example.com'
        inactive_user.password_hash = self.security_service.hash_password('password123')
        inactive_user.is_active = False
        mock_find_by_email.return_value = inactive_user
        
        # Test login with inactive account
        with self.app.test_request_context():
            success, user, error = self.auth_service.login('inactive@example.com', 'password123')
            
            self.assertFalse(success)
            self.assertIsNone(user)
            self.assertEqual(error, "Account is inactive. Please contact an administrator.")

    @patch('app.models.user.User.find_by_id')
    def test_get_current_user(self, mock_find_by_id):
        """Test getting the current user from session."""
        # Configure the mock
        mock_find_by_id.return_value = self.mock_user
        
        # Test with valid session
        with self.app.test_request_context():
            with self.app.test_client() as client:
                with client.session_transaction() as session:
                    session['user_id'] = 1
                    session['last_active'] = int(time.time())  # Fixed from previous implementation
                
                # Test outside the session transaction
                user = self.auth_service.get_current_user()
                self.assertEqual(user, self.mock_user)
                
                # Verify that find_by_id was called with the database and user ID
                mock_find_by_id.assert_called_with(self.mock_db, 1)

    def test_get_current_user_no_session(self):
        """Test getting current user with no session."""
        with self.app.test_request_context():
            user = self.auth_service.get_current_user()
            self.assertIsNone(user)

    @patch('app.models.user.User.find_by_id')
    def test_get_current_user_expired_session(self, mock_find_by_id):
        """Test getting current user with expired session."""
        # Configure the mock
        mock_find_by_id.return_value = self.mock_user
        
        # Test with expired session
        with self.app.test_request_context():
            with self.app.test_client() as client:
                with client.session_transaction() as session:
                    session['user_id'] = 1
                    session['last_active'] = 0  # Way in the past
                
                # Test outside the session transaction
                user = self.auth_service.get_current_user()
                self.assertIsNone(user)

    @patch('app.models.user.User.find_by_id')
    def test_require_role_success(self, mock_find_by_id):
        """Test role check with user having the required role."""
        # Configure the mock with user having 'admin' role
        admin_user = MagicMock(spec=User)
        admin_user.id = 1
        admin_user.roles = ['admin', 'user']
        mock_find_by_id.return_value = admin_user
        
        # Test with valid session and role
        with self.app.test_request_context():
            with self.app.test_client() as client:
                with client.session_transaction() as session:
                    session['user_id'] = 1
                    session['last_active'] = int(time.time())
                
                # Test requiring admin role
                user = self.auth_service.require_role('admin')
                self.assertEqual(user, admin_user)

    @patch('app.models.user.User.find_by_id')
    def test_require_role_failure(self, mock_find_by_id):
        """Test role check with user not having the required role."""
        # Configure the mock with regular user
        mock_find_by_id.return_value = self.mock_user  # Only has 'user' role
        
        # Test with valid session but insufficient role
        with self.app.test_request_context():
            with self.app.test_client() as client:
                with client.session_transaction() as session:
                    session['user_id'] = 1
                    session['last_active'] = int(time.time())
                
                # Test requiring admin role
                user = self.auth_service.require_role('admin')
                self.assertIsNone(user)

    def test_generate_and_validate_api_token(self):
        """Test generating and validating an API token."""
        # Generate a token
        token = self.auth_service.generate_api_token(1, ['read', 'write'])
        
        # Validate the token
        valid, payload = self.auth_service.validate_api_token(token)
        
        # Assertions
        self.assertTrue(valid)
        self.assertEqual(payload['sub'], 1)
        self.assertIn('scopes', payload)
        self.assertIn('read', payload['scopes'])
        self.assertIn('write', payload['scopes'])

    def test_check_token_scope(self):
        """Test checking token scopes."""
        # Test payload with required scope
        payload = {'scopes': ['read', 'write']}
        self.assertTrue(self.auth_service.check_token_scope(payload, 'read'))
        self.assertTrue(self.auth_service.check_token_scope(payload, 'write'))
        self.assertFalse(self.auth_service.check_token_scope(payload, 'admin'))
        
        # Test payload with admin scope (should grant access to all scopes)
        payload = {'scopes': ['admin']}
        self.assertTrue(self.auth_service.check_token_scope(payload, 'read'))
        self.assertTrue(self.auth_service.check_token_scope(payload, 'write'))
        self.assertTrue(self.auth_service.check_token_scope(payload, 'admin'))

    def test_check_csrf_token(self):
        """Test CSRF token validation."""
        with self.app.test_request_context():
            with self.app.test_client() as client:
                with client.session_transaction() as session:
                    # Set a CSRF token in the session
                    token = 'test_csrf_token'
                    session['csrf_token'] = token
                
                # Test with valid token
                self.assertTrue(self.auth_service.check_csrf_token(token))
                
                # Test with invalid token
                self.assertFalse(self.auth_service.check_csrf_token('invalid_token'))

    def test_get_client_ip(self):
        """Test getting client IP from request."""
        # Test with direct IP
        with self.app.test_request_context('/', environ_base={'REMOTE_ADDR': '127.0.0.1'}):
            ip = self.auth_service.get_client_ip()
            self.assertEqual(ip, '127.0.0.1')
        
        # Test with X-Forwarded-For header
        with self.app.test_request_context('/', headers={'X-Forwarded-For': '10.0.0.1, 10.0.0.2'}):
            ip = self.auth_service.get_client_ip()
            self.assertEqual(ip, '10.0.0.1')


if __name__ == '__main__':
    unittest.main()