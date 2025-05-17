"""
Unit tests for the security_utils module.
Tests password hashing, encryption, and validation functions.
"""

import pytest
import base64
from app.utils.security_utils import (
    generate_secure_token,
    generate_fernet_encryption_key,
    hash_password,
    verify_password,
    encrypt_data,
    decrypt_data,
    sanitize_input,
    is_valid_email,
    is_valid_password
)

class TestSecurityUtils:
    """Tests for the security_utils module."""

    def test_generate_secure_token(self):
        """Test generating secure tokens."""
        # Test default length
        token = generate_secure_token()
        assert isinstance(token, str)
        assert len(token) >= 32  # Should be at least the requested length

        # Test custom length
        custom_token = generate_secure_token(64)
        assert isinstance(custom_token, str)
        assert len(custom_token) >= 64

        # Tokens should be different each time
        assert token != generate_secure_token()

    def test_generate_fernet_encryption_key(self):
        """Test generating Fernet encryption keys."""
        key = generate_fernet_encryption_key()
        assert isinstance(key, bytes)
        
        # Should be valid base64
        try:
            base64.urlsafe_b64decode(key)
        except Exception:
            pytest.fail("Key is not valid base64")

    def test_hash_password(self):
        """Test password hashing."""
        password = "SecureP@ss123"
        hashed, salt = hash_password(password)
        
        assert isinstance(hashed, bytes)
        assert isinstance(salt, bytes)
        assert len(hashed) > 0
        assert len(salt) > 0

    def test_verify_password(self):
        """Test password verification."""
        password = "SecureP@ss123"
        wrong_password = "WrongP@ss456"
        
        hashed, salt = hash_password(password)
        
        # Correct password should verify
        assert verify_password(password, hashed, salt) is True
        
        # Incorrect password should fail
        assert verify_password(wrong_password, hashed, salt) is False
        
        # Empty inputs should fail
        assert verify_password("", hashed, salt) is False
        assert verify_password(password, b"", salt) is False
        assert verify_password(password, hashed, b"") is False

    def test_encrypt_decrypt_data(self):
        """Test data encryption and decryption."""
        key = generate_fernet_encryption_key()
        data = "Sensitive information"
        
        # Test string encryption
        encrypted = encrypt_data(data, key)
        assert isinstance(encrypted, bytes)
        assert encrypted != data.encode('utf-8')
        
        # Test decryption
        decrypted = decrypt_data(encrypted, key)
        assert decrypted == data
        
        # Test with bytes input
        bytes_data = b"Bytes data"
        encrypted_bytes = encrypt_data(bytes_data, key)
        decrypted_bytes = decrypt_data(encrypted_bytes, key)
        assert decrypted_bytes == bytes_data.decode('utf-8')
        
        # Test with wrong key
        wrong_key = generate_fernet_encryption_key()
        decrypted_wrong_key = decrypt_data(encrypted, wrong_key)
        assert decrypted_wrong_key is None

    def test_sanitize_input(self):
        """Test input sanitization."""
        # Test HTML escaping
        input_with_html = "<script>alert('XSS')</script>"
        sanitized = sanitize_input(input_with_html)
        assert "<script>" not in sanitized
        assert "&lt;script&gt;" in sanitized
        
        # Test with quotes
        input_with_quotes = "Single ' and double \" quotes"
        sanitized_quotes = sanitize_input(input_with_quotes)
        assert "Single '" not in sanitized_quotes
        assert "double \"" not in sanitized_quotes
        assert "Single &#x27;" in sanitized_quotes
        assert "double &quot;" in sanitized_quotes
        
        # Test with None
        assert sanitize_input(None) == ""
        
        # Test with non-string
        assert isinstance(sanitize_input(123), str)

    def test_is_valid_email(self):
        """Test email validation."""
        # Valid emails
        assert is_valid_email("user@example.com") is True
        assert is_valid_email("user.name@example.co.uk") is True
        assert is_valid_email("user+tag@example.org") is True
        
        # Invalid emails
        assert is_valid_email("") is False
        assert is_valid_email(None) is False
        assert is_valid_email("not_an_email") is False
        assert is_valid_email("user@") is False
        assert is_valid_email("@example.com") is False
        assert is_valid_email("user@domain") is False
        assert is_valid_email("user@.com") is False
        assert is_valid_email("user@domain.") is False
        assert is_valid_email("a" * 65 + "@example.com") is False  # Local part too long

    def test_is_valid_password(self):
        """Test password validation."""
        # Valid passwords
        assert is_valid_password("P@ssw0rd") is True
        assert is_valid_password("Secure123!") is True
        assert is_valid_password("Complex$P@ssw0rd123") is True
        
        # Invalid passwords - too short
        assert is_valid_password("P@ss1") is False
        
        # Invalid passwords - missing uppercase
        assert is_valid_password("password123!") is False
        
        # Invalid passwords - missing lowercase
        assert is_valid_password("PASSWORD123!") is False
        
        # Invalid passwords - missing digit
        assert is_valid_password("Password!") is False
        
        # Invalid passwords - missing special character
        assert is_valid_password("Password123") is False
        
        # Test with custom minimum length
        assert is_valid_password("P@s1", min_length=4) is True
        assert is_valid_password("P@s1", min_length=5) is False
        
        # Test with None or empty
        assert is_valid_password("") is False
        assert is_valid_password(None) is False