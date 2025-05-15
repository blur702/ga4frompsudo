"""
Security related utility functions.

This module provides a collection of helper functions for common security
operations, including:
- Generating cryptographically secure random tokens.
- Generating Fernet encryption keys for symmetric encryption.
- Hashing passwords using a strong algorithm (PBKDF2-HMAC-SHA256).
- Verifying passwords against stored hashes and salts.
- Encrypting and decrypting data using Fernet symmetric encryption.
- Basic input sanitization to mitigate common web vulnerabilities like XSS.
"""

import os
import hashlib
import secrets  # For generating cryptographically strong random numbers
import logging
import base64
from typing import Tuple, Optional, Union  # For type hinting

logger = logging.getLogger(__name__)

# Try to import cryptography.fernet, but don't fail if it's not available
# This allows the module to be imported even if the package is not installed
# Non-encryption functions will still work
try:
    from cryptography.fernet import Fernet, InvalidToken as FernetInvalidToken  # For symmetric encryption
    FERNET_AVAILABLE = True
except ImportError:
    logger.warning("cryptography.fernet package not available. Encryption/decryption functions will be disabled.")
    FERNET_AVAILABLE = False


def generate_secure_token(length: int = 32) -> str:
    """
    Generates a cryptographically secure, URL-safe random text string.

    Args:
        length (int, optional): The desired approximate length of the token.
                            The actual length might vary slightly due to hex encoding.
                            Defaults to 32 characters.

    Returns:
        str: A secure, random, URL-safe text string.
    """
    if length <= 0:
        raise ValueError("Token length must be a positive integer.")
    # secrets.token_urlsafe(nbytes) returns a URL-safe text string,
    # containing nbytes random bytes. Each byte is encoded to 1.33 characters on average.
    # To get an approximate length, adjust nbytes. For hex, nbytes = length // 2.
    # For token_urlsafe, nbytes approx = length * 3/4
    num_bytes = (length * 3) // 4  # Approximate number of bytes for URL-safe token
    if num_bytes == 0:
        num_bytes = 16  # Ensure a minimum byte length

    token = secrets.token_urlsafe(num_bytes)
    logger.debug(f"Generated secure token of length {len(token)} (requested approx {length}).")
    return token


def generate_fernet_encryption_key() -> bytes:
    """
    Generates a new Fernet encryption key.
    Fernet keys are URL-safe base64-encoded.

    Returns:
        bytes: A new Fernet encryption key.
    """
    if not FERNET_AVAILABLE:
        logger.warning("Fernet is not available. Returning a dummy key for development only.")
        # Generate a replacement key that looks like a Fernet key but is not usable
        # This is just to avoid breaking code that expects a key, in development
        return base64.urlsafe_b64encode(os.urandom(32))

    key = Fernet.generate_key()
    logger.info("New Fernet encryption key generated.")
    return key


def hash_password(password: str, salt: Optional[bytes] = None) -> Tuple[bytes, bytes]:
    """
    Hashes a password using PBKDF2-HMAC-SHA256.

    A new salt is generated if one is not provided. It's crucial to store
    both the hash and the salt securely for later verification.

    Args:
        password (str): The plain-text password to hash.
        salt (Optional[bytes], optional): An optional salt to use for hashing.
                                      If None, a new salt will be generated.
                                      Recommended to always generate a new salt for new passwords.
                                      Defaults to None.

    Returns:
        Tuple[bytes, bytes]: A tuple containing (hashed_password, salt_used).

    Raises:
        ValueError: If the password is empty.
    """
    if not password:
        raise ValueError("Password cannot be empty.")

    if salt is None:
        salt = os.urandom(16)  # Generate a new 16-byte salt
        logger.debug("New salt generated for password hashing.")

    # Parameters for PBKDF2:
    # - 'sha256': The hash digest algorithm.
    # - password.encode('utf-8'): The password, encoded to bytes.
    # - salt: The salt.
    # - 310000: Iteration count (OWASP recommendation for PBKDF2-HMAC-SHA256 in 2023)
    #           adjust based on performance and security needs.
    iterations = 310000  # Increased iterations for better security

    hashed_key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        iterations
        # dklen=32 # Optionally specify derived key length, default is good for SHA256
    )
    logger.info("Password hashed successfully.")
    return hashed_key, salt


def verify_password(password_to_check: str, stored_hash: bytes, salt: bytes) -> bool:
    """
    Verifies a plain-text password against a stored hash and salt.

    Args:
        password_to_check (str): The plain-text password to verify.
        stored_hash (bytes): The previously stored hash of the correct password.
        salt (bytes): The salt that was used when `stored_hash` was generated.

    Returns:
        bool: True if the `password_to_check` matches the `stored_hash` (using the `salt`),
              False otherwise.
    """
    if not password_to_check or not stored_hash or not salt:
        logger.warning("Attempted to verify password with empty password, hash, or salt.")
        return False  # Cannot verify if essential components are missing

    # Hash the password_to_check using the same salt and parameters
    new_hash, _ = hash_password(password_to_check, salt)

    # Compare the new hash with the stored hash using secrets.compare_digest
    # to protect against timing attacks.
    is_match = secrets.compare_digest(new_hash, stored_hash)
    if is_match:
        logger.info("Password verification successful.")
    else:
        logger.warning("Password verification failed.")
    return is_match


def encrypt_data(data: Union[str, bytes], fernet_key: bytes) -> Optional[bytes]:
    """
    Encrypts data using Fernet symmetric encryption.

    Args:
        data (Union[str, bytes]): The data to encrypt. If string, it will be UTF-8 encoded.
        fernet_key (bytes): The Fernet encryption key (generated by `generate_fernet_encryption_key`).

    Returns:
        Optional[bytes]: The encrypted data (as bytes), or None if encryption fails.
    """
    if not FERNET_AVAILABLE:
        logger.error("Fernet is not available. Cannot encrypt data.")
        return None

    if not data:
        logger.warning("Attempted to encrypt empty data.")
        return None  # Or b'' depending on desired behavior for empty input
    if not fernet_key:
        logger.error("Fernet key is missing for data encryption.")
        return None

    try:
        f = Fernet(fernet_key)
        data_bytes = data.encode('utf-8') if isinstance(data, str) else data
        encrypted_data = f.encrypt(data_bytes)
        logger.debug("Data encrypted successfully.")
        return encrypted_data
    except Exception as e:  # Catch specific exceptions if possible
        logger.error(f"Data encryption failed: {e}", exc_info=True)
        return None


def decrypt_data(encrypted_token: bytes, fernet_key: bytes, ttl: Optional[int] = None) -> Optional[str]:
    """
    Decrypts data using Fernet symmetric encryption.

    Args:
        encrypted_token (bytes): The encrypted data token (as bytes) to decrypt.
        fernet_key (bytes): The Fernet encryption key used for encryption.
        ttl (Optional[int]): Time-to-live in seconds for the token. If the token is older
                         than ttl seconds, decryption will fail (if Fernet was used with TTL).

    Returns:
        Optional[str]: The decrypted data as a UTF-8 string, or None if decryption fails
                       (e.g., invalid key, corrupted token, expired TTL).
    """
    if not FERNET_AVAILABLE:
        logger.error("Fernet is not available. Cannot decrypt data.")
        return None

    if not encrypted_token:
        logger.warning("Attempted to decrypt an empty token.")
        return None
    if not fernet_key:
        logger.error("Fernet key is missing for data decryption.")
        return None

    try:
        f = Fernet(fernet_key)
        if ttl is not None:
            decrypted_bytes = f.decrypt(encrypted_token, ttl=ttl)
        else:
            decrypted_bytes = f.decrypt(encrypted_token)

        decrypted_string = decrypted_bytes.decode('utf-8')
        logger.debug("Data decrypted successfully.")
        return decrypted_string
    except Exception as e:  # Catch FernetInvalidToken and other errors
        if FERNET_AVAILABLE and isinstance(e, FernetInvalidToken):
            logger.warning("Data decryption failed: Invalid or expired token.")
        else:
            logger.error(f"Data decryption failed with an unexpected error: {e}", exc_info=True)
        return None


def sanitize_input(input_str: str) -> str:
    """
    Sanitizes user input to prevent common web vulnerabilities, primarily Cross-Site Scripting (XSS).
    This is a very basic sanitizer; for robust XSS protection, use a dedicated library
    like Bleach, especially if allowing any HTML.

    This implementation focuses on escaping characters that have special meaning in HTML.

    Args:
        input_str (str): The input string to sanitize.

    Returns:
        str: The sanitized string with special HTML characters escaped.
             Returns an empty string if input is None or not a string.
    """
    if input_str is None:
        return ""
    if not isinstance(input_str, str):
        logger.warning(f"sanitize_input received non-string type: {type(input_str)}. Converting to string.")
        input_str = str(input_str)

    # Basic HTML character escaping
    # In a real application, especially one allowing rich text, use a library like Bleach.
    sanitized = input_str.replace('&', '&amp;') \
                       .replace('<', '&lt;') \
                       .replace('>', '&gt;') \
                       .replace('"', '&quot;') \
                       .replace("'", '&#x27;')  # &#39; or &#x27; for single quote
    return sanitized


def is_valid_email(email: str) -> bool:
    """
    Validates an email address format using basic rules.
    This is a simple validator - for production, consider more robust libraries.
    
    Args:
        email (str): The email address to validate.
        
    Returns:
        bool: True if the email format appears valid, False otherwise.
    """
    if not email or not isinstance(email, str):
        return False
        
    # Simple validation: contains @ with text before and after, and a period in the domain
    if '@' not in email:
        return False
        
    local, domain = email.rsplit('@', 1)
    
    # Check local part (before @)
    if not local or len(local) > 64:  # Local part max length per RFC
        return False
        
    # Check domain part (after @)
    if not domain or '.' not in domain:
        return False
        
    # Check if domain has at least one character before and after the period
    parts = domain.split('.')
    if len(parts) < 2 or any(not part for part in parts):
        return False
        
    # Check TLD isn't all numeric
    if parts[-1].isdigit():
        return False
        
    logger.debug(f"Email validation successful for: {email}")
    return True


def is_valid_password(password: str, min_length: int = 8) -> bool:
    """
    Validates a password against basic security requirements.
    
    Args:
        password (str): The password to validate.
        min_length (int, optional): The minimum required password length. Defaults to 8.
        
    Returns:
        bool: True if the password meets all requirements, False otherwise.
    """
    if not password or not isinstance(password, str):
        return False
        
    # Check length
    if len(password) < min_length:
        logger.debug(f"Password rejected: too short (length={len(password)}, min={min_length})")
        return False
        
    # Check for at least one uppercase letter
    if not any(char.isupper() for char in password):
        logger.debug("Password rejected: missing uppercase letter")
        return False
        
    # Check for at least one lowercase letter
    if not any(char.islower() for char in password):
        logger.debug("Password rejected: missing lowercase letter")
        return False
        
    # Check for at least one digit
    if not any(char.isdigit() for char in password):
        logger.debug("Password rejected: missing digit")
        return False
        
    # Check for at least one special character
    special_chars = "!@#$%^&*()-_=+[]{}|;:'\",.<>/?"
    if not any(char in special_chars for char in password):
        logger.debug("Password rejected: missing special character")
        return False
        
    logger.debug("Password validation successful")
    return True