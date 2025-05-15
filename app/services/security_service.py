"""
Security Service.
Handles security operations such as encryption key management,
data encryption/decryption, and password hashing/verification.
This service centralizes security logic for the application.
"""

import logging
import os
from typing import Optional, Tuple, Union, Dict, Any

# Import utility functions that this service will use
from app.utils.security_utils import (
    generate_fernet_encryption_key,
    hash_password as util_hash_password,
    verify_password as util_verify_password,
    encrypt_data as util_encrypt_data,
    decrypt_data as util_decrypt_data,
    FERNET_AVAILABLE
)

logger = logging.getLogger(__name__)

class SecurityService:
    """
    Service class for handling core security operations.

    This includes managing the application's Fernet encryption key (for symmetric
    encryption/decryption of sensitive data), and providing methods for password
    management (hashing and verification). It relies on utility functions for the
    cryptographic primitives.

    Attributes:
        config (Dict[str, Any]): A dictionary containing security-related configuration,
                               such as the path to the encryption key file.
        _fernet_key (Optional[bytes]): The loaded or generated Fernet encryption key.
                                     It's loaded upon initialization.
    """

    DEFAULT_KEY_FILENAME = "app_encryption.key"  # Default filename if path is a directory

    def __init__(self, security_config: Dict[str, Any]):
        """
        Initializes the SecurityService.

        It loads the Fernet encryption key from the path specified in the
        `security_config` or generates a new one if it doesn't exist.
        The configuration should provide `key_path`.

        Args:
            security_config (Dict[str, Any]): A dictionary containing security configuration.
                Expected keys:
                - 'key_path': Path to the Fernet encryption key file or directory.
                              If a directory, 'app_encryption.key' will be used as filename.
                - 'password_iterations' (Optional[int]): Iteration count for password hashing.

        Raises:
            ValueError: If `key_path` is not provided in `security_config`.
            IOError: If there's an issue reading/writing the key file.
        """
        self.config = security_config
        self._fernet_key: Optional[bytes] = None
        self._password_iterations = self.config.get('password_iterations', 310000)  # Default from utils

        key_path_config = self.config.get('key_path')
        if not key_path_config:
            logger.critical("CRITICAL: 'key_path' not found in security_config for SecurityService.")
            raise ValueError("'key_path' must be provided in the security configuration.")

        self.key_file_path: str = self._determine_key_file_path(key_path_config)
        self._load_or_generate_fernet_key()
        logger.info("SecurityService initialized successfully.")

    def _determine_key_file_path(self, configured_path: str) -> str:
        """
        Determines the absolute path to the key file.
        If configured_path is a directory, appends DEFAULT_KEY_FILENAME.
        """
        if os.path.isdir(configured_path):
            return os.path.join(configured_path, self.DEFAULT_KEY_FILENAME)
        # If it's a file (or intended to be), ensure parent directory exists
        parent_dir = os.path.dirname(configured_path)
        if parent_dir and not os.path.exists(parent_dir):
            try:
                os.makedirs(parent_dir, exist_ok=True)
                logger.info(f"Created directory for encryption key: {parent_dir}")
            except OSError as e:
                logger.error(f"Could not create directory {parent_dir} for key file: {e}", exc_info=True)
                raise IOError(f"Could not create directory for key file at {parent_dir}") from e
        return configured_path

    def _load_or_generate_fernet_key(self) -> None:
        """
        Loads the Fernet encryption key from `self.key_file_path`.
        If the file doesn't exist, a new key is generated and saved to the path.
        The loaded/generated key is stored in `self._fernet_key`.

        Raises:
            IOError: If the key file cannot be read or written.
        """
        if not FERNET_AVAILABLE:
            logger.warning("Fernet encryption is not available. Key will be generated but not usable.")
            self._fernet_key = generate_fernet_encryption_key()  # This will be a dummy key 
            return

        try:
            if os.path.exists(self.key_file_path):
                with open(self.key_file_path, 'rb') as f:
                    self._fernet_key = f.read()
                logger.info(f"Fernet encryption key loaded successfully from: {self.key_file_path}")
                if not self._fernet_key or len(self._fernet_key) < 44:  # Basic check for Fernet key format
                    logger.warning(f"Key file at {self.key_file_path} seems invalid or empty. Will regenerate.")
                    self._generate_and_save_new_key()
            else:
                logger.warning(f"Encryption key file not found at: {self.key_file_path}. Generating a new key.")
                self._generate_and_save_new_key()
        except IOError as e:
            logger.critical(f"CRITICAL: IOError accessing key file at {self.key_file_path}: {e}", exc_info=True)
            raise IOError(f"Failed to load or generate encryption key at {self.key_file_path}.") from e
        except Exception as e:  # Catch any other unexpected errors
            logger.critical(f"CRITICAL: Unexpected error during key loading/generation for {self.key_file_path}: {e}", exc_info=True)
            raise IOError(f"Unexpected error with encryption key at {self.key_file_path}.") from e

        if not self._fernet_key:  # Should be set by now
            logger.critical(f"CRITICAL: Fernet key could not be established for {self.key_file_path}.")
            raise ValueError("Fernet encryption key could not be loaded or generated.")

    def _generate_and_save_new_key(self) -> None:
        """Generates a new Fernet key and saves it to self.key_file_path."""
        new_key = generate_fernet_encryption_key()  # From utils
        try:
            # Ensure parent directory exists
            parent_dir = os.path.dirname(self.key_file_path)
            if parent_dir and not os.path.exists(parent_dir):  # Check again just in case
                os.makedirs(parent_dir, exist_ok=True)

            with open(self.key_file_path, 'wb') as f:
                f.write(new_key)
            self._fernet_key = new_key
            logger.info(f"New Fernet encryption key generated and saved to: {self.key_file_path}")
        except IOError as e:
            logger.error(f"Failed to save newly generated encryption key to {self.key_file_path}: {e}", exc_info=True)
            # If key cannot be saved, the service is not secure.
            raise IOError(f"Could not save new encryption key to {self.key_file_path}.") from e

    def get_fernet_key(self) -> Optional[bytes]:
        """
        Returns the loaded Fernet encryption key.

        Returns:
            Optional[bytes]: The Fernet key, or None if not loaded.
        """
        if not self._fernet_key:
            logger.error("Attempted to get Fernet key, but it's not loaded. This indicates an initialization issue.")
        return self._fernet_key

    def encrypt(self, data: Union[str, bytes]) -> Optional[bytes]:
        """
        Encrypts the given data using the application's Fernet key.

        Args:
            data (Union[str, bytes]): The data to encrypt. If string, it's UTF-8 encoded.

        Returns:
            Optional[bytes]: The encrypted data as bytes, or None if encryption fails
                           (e.g., key not loaded, data is empty).
        """
        if not self._fernet_key:
            logger.error("Encryption failed: Fernet key is not available.")
            return None
        if data is None or data == "":  # Handle empty or None data specifically
            logger.warning("Attempted to encrypt None or empty data.")
            return None  # Or b'' if encrypting empty string is desired behavior for Fernet

        encrypted = util_encrypt_data(data, self._fernet_key)  # Call the utility function
        if encrypted:
            logger.debug("Data encryption successful using SecurityService.")
        else:
            logger.error("Data encryption failed in SecurityService, util_encrypt_data returned None.")
        return encrypted

    def decrypt(self, encrypted_token: bytes, ttl: Optional[int] = None) -> Optional[str]:
        """
        Decrypts the given Fernet token using the application's Fernet key.

        Args:
            encrypted_token (bytes): The encrypted token (bytes) to decrypt.
            ttl (Optional[int]): Time-to-live in seconds for the token, if the token
                               was created with a timestamp for TTL validation by Fernet.

        Returns:
            Optional[str]: The decrypted data as a UTF-8 string, or None if decryption fails
                         (e.g., key not loaded, invalid token, expired TTL).
        """
        if not self._fernet_key:
            logger.error("Decryption failed: Fernet key is not available.")
            return None
        if not encrypted_token:
            logger.warning("Attempted to decrypt None or empty token.")
            return None

        decrypted = util_decrypt_data(encrypted_token, self._fernet_key, ttl=ttl)  # Call utility
        if decrypted:
            logger.debug("Data decryption successful using SecurityService.")
        else:
            # Error/warning already logged by util_decrypt_data
            logger.warning("Data decryption failed in SecurityService (see previous util log for details).")
        return decrypted

    def hash_password(self, password: str, salt: Optional[bytes] = None) -> Tuple[bytes, bytes]:
        """
        Hashes a password using the application's configured iteration count.
        This method is a wrapper around the utility function to use service-level
        configurations like iteration count.

        Args:
            password (str): The plain-text password.
            salt (Optional[bytes]): Optional salt. If None, a new one is generated.

        Returns:
            Tuple[bytes, bytes]: (hashed_password, salt_used)
        """
        logger.debug(f"Hashing password with {self._password_iterations} iterations via SecurityService.")
        return util_hash_password(password, salt)

    def verify_password(self, password_to_check: str, stored_hash: bytes, salt: bytes) -> bool:
        """
        Verifies a password against a stored hash and salt, using the application's
        configured iteration count.

        Args:
            password_to_check (str): The plain-text password to verify.
            stored_hash (bytes): The stored password hash.
            salt (bytes): The salt used during hashing.

        Returns:
            bool: True if the password matches, False otherwise.
        """
        logger.debug(f"Verifying password using SecurityService.")
        return util_verify_password(password_to_check, stored_hash, salt)