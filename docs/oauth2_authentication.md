# OAuth2 Authentication for GA4

This document explains how to use OAuth2 authentication for accessing Google Analytics 4 (GA4) data.

## Overview

The application supports two authentication methods for GA4:

1. **Service Account Authentication** - Uses a JSON key file for authentication
2. **OAuth2 Authentication** - Uses user-based authorization with refresh tokens

OAuth2 authentication provides access to all properties the authorized user has permission to view, while service account authentication is limited to properties where the service account has been explicitly granted access.

## Authentication Workflow

### OAuth2 Authentication Flow

1. **Configure OAuth2 Client ID and Secret**
   - Set up in Google Cloud Console
   - Add these to the application through the admin interface

2. **Authorize with Google**
   - Redirect to Google for authorization
   - Google redirects back with an authorization code
   - Application exchanges code for access and refresh tokens
   - Tokens are stored securely in the database

3. **Ongoing Access**
   - Application uses refresh tokens to generate new access tokens
   - No user interaction needed after initial setup

## Configuration

### Prerequisites

1. Google Cloud Project with Analytics API enabled
2. OAuth2 client ID and secret from Google Cloud Console
3. Administrator access to the application

### Setup Steps

1. **Access the Admin Panel**
   - Navigate to `/admin/ga4-config`

2. **Select OAuth2 Authentication Method**
   - Choose "OAuth2" as the authentication method

3. **Enter OAuth2 Credentials**
   - Enter your client ID and client secret
   - Save the configuration

4. **Complete Authorization**
   - Click "Authorize with Google"
   - Sign in to Google and grant permissions
   - You'll be redirected back to the application

5. **Verify Authorization**
   - Check that the OAuth2 status shows as "fully configured and authorized"

## Property Syncing with OAuth2

When using OAuth2 authentication, the property sync will:

1. Fetch all GA4 properties the authorized user has access to
2. Store them in the local database
3. Enable analytics data retrieval (which uses the service account)

### Syncing Properties

To sync properties using OAuth2:

1. **Ensure OAuth2 is configured correctly**
   - Check that authorization is complete on the GA4 configuration page

2. **Perform Sync**
   - Go to the Admin Properties page (`/admin/properties`)
   - Click "Sync All Properties"
   - Wait for the sync to complete
   - You should see all your GA4 properties listed

3. **Command Line Sync**
   - Alternatively, use the sync script:
   ```bash
   python sync_properties.py
   ```

## Hybrid Authentication Model

The application uses a hybrid authentication model:

- **OAuth2**: Used for property discovery and synchronization
- **Service Account**: Used for analytics data retrieval

This approach provides the best balance:
- OAuth2 gives access to all properties you can see in Google Analytics
- Service account provides more reliable background data access

## Troubleshooting

### OAuth2 Authorization Failed

If authorization fails:
- Check that your client ID and secret are correct
- Verify that redirect URIs are properly configured in Google Cloud Console
- Check that the Google account has access to the GA4 properties

### Only One Property Showing

If only one property is synced despite using OAuth2:
- Verify OAuth2 status shows "fully configured and authorized"
- Check the app logs for OAuth2 token errors
- Try re-authorizing by clicking "Authorize with Google" again

### OAuth2 Tokens Expired

If tokens expire:
- The application should automatically refresh tokens
- If issues persist, re-authorize by clicking "Authorize with Google"

## Security Considerations

OAuth2 tokens are stored securely in the database and are handled according to security best practices:

- Access tokens are short-lived (typically 1 hour)
- Refresh tokens are stored securely
- All communication uses HTTPS
- Token validation happens on every request