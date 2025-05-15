# Secure Keys Directory

This directory is intended for secure keys and credentials files required by the application.

## Files to Store Here

1. **encryption.key**: Encryption key for sensitive data
2. **ga4-service-account.json**: Google Analytics 4 service account credentials

## Important Security Notice

- **Never commit these files to version control!**
- This directory is included in `.gitignore` to prevent accidental commits
- Keep backup copies of these files in a secure location
- In production, consider using a secure key management service instead of files

## Creating Keys

### Generate encryption.key

To generate a new encryption key, run:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" > keys/encryption.key
```

### GA4 Service Account

1. Create a service account in the Google Cloud Console
2. Enable the Google Analytics API
3. Grant the service account appropriate access to your GA4 properties
4. Download the service account JSON key and save it as `ga4-service-account.json` in this directory