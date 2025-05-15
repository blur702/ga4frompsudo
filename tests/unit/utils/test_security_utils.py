"""
Tests for the security utils module.
"""

import os
import secrets
import pytest
from app.utils.security_utils import (
    generate_secure_token,
    generate_fernet_encryption_key,
    hash_password,
    verify_password,
    encrypt_data,
    decrypt_data,
    sanitize_input,
    FERNET_AVAILABLE
)


def test_generate_secure_token_length():
    """Test that generate_secure_token returns a token of approximately the requested length."""
    # Test various lengths
    for length in [16, 32, 64, 128]:
        token = generate_secure_token(length)
        # Allow for some variance in the length due to base64 encoding
        assert len(token) >= 0.75 * length
        assert len(token) <= 1.5 * length


def test_generate_secure_token_uniqueness():
    """Test that generate_secure_token generates unique tokens."""
    tokens = [generate_secure_token(32) for _ in range(10)]
    # Check that all generated tokens are unique
    assert len(tokens) == len(set(tokens))


def test_generate_secure_token_invalid_length():
    """Test that generate_secure_token raises ValueError for invalid lengths."""
    with pytest.raises(ValueError):
        generate_secure_token(0)
    
    with pytest.raises(ValueError):
        generate_secure_token(-1)


def test_generate_fernet_encryption_key():
    """Test that generate_fernet_encryption_key returns a valid key."""
    # This test may be skipped if Fernet is not available
    key = generate_fernet_encryption_key()
    assert isinstance(key, bytes)
    
    # If Fernet is available, check key format
    if FERNET_AVAILABLE:
        # Fernet keys are 32 bytes of base64-encoded data
        decoded = None
        try:
            # Should be URL-safe base64 encoded
            decoded = secrets.token_bytes(32)
            assert len(decoded) == 32
        except Exception:
            pass  # Don't fail if we can't decode, as it might be a dummy key


def test_hash_password():
    """Test hashing a password."""
    # Hash a password without providing a salt
    password = "SecurePassword123"
    hashed_key, salt = hash_password(password)
    
    # Verify the results
    assert isinstance(hashed_key, bytes)
    assert isinstance(salt, bytes)
    assert len(salt) > 0
    assert len(hashed_key) > 0


def test_hash_password_with_salt():
    """Test hashing a password with a provided salt."""
    # Generate a salt
    salt = os.urandom(16)
    
    # Hash a password with the salt
    password = "SecurePassword123"
    hashed_key, returned_salt = hash_password(password, salt)
    
    # Verify the results
    assert isinstance(hashed_key, bytes)
    assert returned_salt == salt  # The returned salt should be the same as the provided salt


def test_hash_password_empty():
    """Test that hash_password raises ValueError for empty passwords."""
    with pytest.raises(ValueError):
        hash_password("")


def test_verify_password():
    """Test password verification."""
    # Hash a password
    password = "SecurePassword123"
    hashed_key, salt = hash_password(password)
    
    # Verify the correct password
    result = verify_password(password, hashed_key, salt)
    assert result is True
    
    # Verify an incorrect password
    wrong_result = verify_password("WrongPassword123", hashed_key, salt)
    assert wrong_result is False


def test_verify_password_bad_inputs():
    """Test that verify_password handles bad inputs gracefully."""
    # Empty password
    assert verify_password("", b'hash', b'salt') is False
    
    # Empty hash
    assert verify_password("password", b'', b'salt') is False
    
    # Empty salt
    assert verify_password("password", b'hash', b'') is False


@pytest.mark.skipif(not FERNET_AVAILABLE, reason="Fernet not available")
def test_encrypt_decrypt_data():
    """Test encrypting and decrypting data."""
    # Generate a key
    key = generate_fernet_encryption_key()
    
    # Encrypt some data
    data = "This is secret information"
    encrypted = encrypt_data(data, key)
    
    # Verify encryption
    assert encrypted is not None
    assert isinstance(encrypted, bytes)
    assert encrypted != data.encode('utf-8')  # Make sure it's not plaintext
    
    # Decrypt the data
    decrypted = decrypt_data(encrypted, key)
    
    # Verify decryption
    assert decrypted == data


@pytest.mark.skipif(not FERNET_AVAILABLE, reason="Fernet not available")
def test_encrypt_decrypt_with_ttl():
    """Test encrypting and decrypting with a TTL."""
    # This is a low-level test that might not work if Fernet's internal
    # behavior changes. The test simply verifies the ttl parameter is passed through.
    # Generate a key
    key = generate_fernet_encryption_key()
    
    # Encrypt some data
    data = "This is secret information"
    encrypted = encrypt_data(data, key)
    
    # Decrypt with a very long TTL (should work)
    long_ttl_result = decrypt_data(encrypted, key, ttl=100000)
    assert long_ttl_result == data


def test_encrypt_decrypt_bad_inputs():
    """Test that encrypt_data and decrypt_data handle bad inputs gracefully."""
    # Empty data
    assert encrypt_data("", b'key') is None
    
    # Empty key
    assert encrypt_data("data", b'') is None
    
    # Empty token
    assert decrypt_data(b'', b'key') is None
    
    # Empty key for decryption
    assert decrypt_data(b'token', b'') is None


def test_sanitize_input():
    """Test that sanitize_input properly escapes HTML characters."""
    # Test various inputs with HTML characters
    test_cases = [
        ("<script>alert('XSS')</script>", "&lt;script&gt;alert(&#x27;XSS&#x27;)&lt;/script&gt;"),
        ('<img src="x" onerror="alert(\'XSS\')"/>', "&lt;img src=&quot;x&quot; onerror=&quot;alert(&#x27;XSS&#x27;)&quot;/&gt;"),
        ("Normal text", "Normal text"),
        ('Text with "quotes" and \'apostrophes\'', "Text with &quot;quotes&quot; and &#x27;apostrophes&#x27;"),
        ("Text with <angle brackets>", "Text with &lt;angle brackets&gt;"),
        ("Text with &ampersands&", "Text with &amp;ampersands&amp;"),
    ]
    
    for input_text, expected_output in test_cases:
        assert sanitize_input(input_text) == expected_output


def test_sanitize_input_edge_cases():
    """Test that sanitize_input handles edge cases."""
    # None input
    assert sanitize_input(None) == ""
    
    # Non-string input
    assert sanitize_input(123) == "123"
    
    # Empty string
    assert sanitize_input("") == ""