#!/usr/bin/env python
"""
Script to generate a secure encryption key for the GA4 Analytics Dashboard.

This script:
1. Creates a new Fernet encryption key
2. Saves it to the specified file path
3. Sets appropriate file permissions (0600 on Unix-like systems)

Usage: python generate_key.py [output_path]
"""

import os
import sys
import stat
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from cryptography.fernet import Fernet
    FERNET_AVAILABLE = True
except ImportError:
    logger.warning("Cryptography package not installed. Please install with: pip install cryptography")
    FERNET_AVAILABLE = False


def generate_encryption_key():
    """Generate a new Fernet encryption key."""
    if not FERNET_AVAILABLE:
        logger.error("Cannot generate key: cryptography package not available")
        return None
        
    try:
        return Fernet.generate_key()
    except Exception as e:
        logger.error(f"Error generating encryption key: {e}")
        return None


def save_key_to_file(key, file_path):
    """
    Save the encryption key to a file and set appropriate permissions.
    
    Args:
        key: The encryption key bytes
        file_path: Path where to save the key
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Write the key to the file
        with open(file_path, 'wb') as f:
            f.write(key)
        
        # Set file permissions to be readable only by the owner (0600)
        # This is crucial for security on Unix-like systems
        try:
            os.chmod(file_path, stat.S_IRUSR | stat.S_IWUSR)
        except Exception as e:
            logger.warning(f"Could not set file permissions: {e}")
            
        logger.info(f"Encryption key saved to: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving encryption key: {e}")
        return False


def main():
    """Main function to generate and save the encryption key."""
    # Determine output path
    if len(sys.argv) > 1:
        output_path = sys.argv[1]
    else:
        output_path = os.path.join('keys', 'encryption.key')
    
    # Generate the key
    logger.info("Generating new encryption key...")
    key = generate_encryption_key()
    if not key:
        sys.exit(1)
    
    # Save the key
    logger.info(f"Saving key to {output_path}...")
    if save_key_to_file(key, output_path):
        logger.info("Key generation completed successfully")
        logger.info("IMPORTANT: Keep this key secure and never commit it to version control!")
    else:
        logger.error("Failed to save the encryption key")
        sys.exit(1)


if __name__ == '__main__':
    main()