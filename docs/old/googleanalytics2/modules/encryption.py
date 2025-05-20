import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from flask import current_app

# Environment variable for additional entropy
ENV_ENCRYPTION_SALT = 'GA4_ENCRYPTION_SALT'

def get_encryption_key():
    """
    Get or generate the encryption key.
    
    Returns:
        bytes: The encryption key.
    """
    # Check if encryption key is stored in the database
    from modules.models import Setting
    
    # Try to get the encryption key from the database
    stored_key = Setting.query.filter_by(key='encryption_key').first()
    
    if stored_key and stored_key.value:
        # Use the stored key
        return base64.urlsafe_b64decode(stored_key.value.encode())
    else:
        # Generate a new key
        # Use a combination of app secret key and environment variable for better security
        secret_key = current_app.config['SECRET_KEY']
        env_salt = os.environ.get(ENV_ENCRYPTION_SALT, 'default_salt_change_in_production')
        
        # Use PBKDF2 to derive a key
        salt = os.urandom(16)  # Generate a random salt
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = kdf.derive((secret_key + env_salt).encode())
        
        # Store the key in the database (encoded as base64)
        key_b64 = base64.urlsafe_b64encode(key).decode()
        new_key = Setting(
            key='encryption_key',
            value=key_b64,
            description='Encryption key for sensitive data',
            is_encrypted=False  # The key itself is not encrypted
        )
        
        from modules.models import db
        db.session.add(new_key)
        db.session.commit()
        
        current_app.logger.info("Generated and stored new encryption key")
        
        return key

def encrypt_value(value):
    """
    Encrypt a value using AES-GCM authenticated encryption.
    
    Args:
        value (str): The value to encrypt.
        
    Returns:
        str: The encrypted value as a base64-encoded string.
    """
    if not value:
        return None
    
    try:
        # Get the encryption key
        key = get_encryption_key()
        
        # Generate a random nonce
        nonce = os.urandom(12)
        
        # Create an AES-GCM cipher
        aesgcm = AESGCM(key)
        
        # Encrypt the value with authentication
        value_bytes = value.encode()
        encrypted_value = aesgcm.encrypt(nonce, value_bytes, None)
        
        # Combine nonce and encrypted value for storage
        result = nonce + encrypted_value
        
        # Return as base64 string
        return base64.b64encode(result).decode()
    except Exception as e:
        current_app.logger.error(f"Error encrypting value: {e}")
        return None

def decrypt_value(encrypted_value):
    """
    Decrypt a value that was encrypted using AES-GCM authenticated encryption.
    
    Args:
        encrypted_value (str): The encrypted value as a base64-encoded string.
        
    Returns:
        str: The decrypted value, or None if decryption fails.
    """
    if not encrypted_value:
        return None
    
    try:
        # Get the encryption key
        key = get_encryption_key()
        
        # Decode from base64
        decoded_value = base64.b64decode(encrypted_value)
        
        # Extract nonce and ciphertext
        nonce = decoded_value[:12]
        ciphertext = decoded_value[12:]
        
        # Create an AES-GCM cipher
        aesgcm = AESGCM(key)
        
        # Decrypt the value
        decrypted_value = aesgcm.decrypt(nonce, ciphertext, None)
        
        return decrypted_value.decode()
    except Exception as e:
        current_app.logger.error(f"Error decrypting value: {e}")
        return None