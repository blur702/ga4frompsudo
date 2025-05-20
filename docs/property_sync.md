# GA4 Property Sync Documentation

This document explains how to use the property synchronization functionality to manage GA4 properties and their associated websites in your local database.

## Overview

The property sync functionality allows you to:
- Fetch all GA4 properties from your Google Analytics accounts
- Sync properties and their websites (data streams) to your local database
- Manage properties through a web interface or command-line tools
- Keep your local database in sync with GA4 API

## Components

### 1. PropertySyncService

The core service that handles all synchronization operations:
- Located at: `app/services/property_sync_service.py`
- Provides methods to sync all properties or individual properties
- Handles both properties and their associated websites/data streams

### 2. Command-Line Tool

A standalone script for syncing properties from the command line:
- Located at: `sync_properties.py`
- Run with various options to control syncing behavior

### 3. Web Interface

Admin interface for managing properties:
- URL: `/admin/properties`
- Provides visual interface to view and sync properties
- Shows current sync status and allows individual property syncing

## Usage

### Command-Line Sync

#### Sync All Properties
```bash
python sync_properties.py
```

#### Sync a Single Property
```bash
python sync_properties.py --single-property 123456789
```

#### View Current Sync Status
```bash
python sync_properties.py --summary-only
```

#### Skip Website Syncing
```bash
python sync_properties.py --no-websites
```

#### Skip Updating Existing Records
```bash
python sync_properties.py --skip-existing
```

#### Save Results to Files
```bash
python sync_properties.py --output-json results.json --output-csv summary.csv
```

### Web Interface

1. **Access Property Management**
   - Navigate to `/admin` in your browser
   - Click on "Manage Properties"

2. **Sync All Properties**
   - Click the "Sync All Properties" button
   - Wait for the sync to complete
   - Page will refresh showing updated data

3. **Sync Individual Property**
   - Find the property in the list
   - Click the "Sync" button for that property
   - Updates only that specific property and its websites

## Data Model

### Properties
- **property_id**: GA4 property identifier (e.g., "properties/123456789")
- **property_name**: Display name of the property
- **account_id**: Associated GA4 account ID
- **create_time**: When the property was created in GA4
- **update_time**: Last update time in GA4

### Websites
- **website_id**: GA4 data stream identifier
- **property_db_id**: Link to parent property in database
- **website_url**: The website URL
- **create_time**: When the data stream was created
- **update_time**: Last update time

## API Integration

The sync service uses the following GA4 APIs:
- **Analytics Admin API**: For property and data stream management
- **Analytics Data API**: For report data (if needed)

Required scopes:
- `https://www.googleapis.com/auth/analytics.readonly`

### Authentication Methods

The property sync service supports two authentication methods:

1. **Service Account Authentication**
   - Uses a service account key file for API access
   - Limited to properties where the service account has been explicitly granted access
   - Good for background processing and automation

2. **OAuth2 Authentication**
   - Uses user-authorized access to Google Analytics
   - Can access all properties the authorized user has access to
   - Requires initial user authorization flow
   - Recommended for comprehensive property syncing

For details on setting up OAuth2 authentication, see [OAuth2 Authentication](oauth2_authentication.md).

## Error Handling

The sync service handles various error conditions:
- Missing GA4 credentials
- API rate limits
- Network errors
- Database conflicts

All errors are logged and reported in the sync results.

## Best Practices

1. **Initial Sync**
   - Run a full sync when first setting up
   - Use `--output-json` to save a backup of results

2. **Regular Updates**
   - Schedule periodic syncs to keep data current
   - Use cron jobs for automated syncing

3. **Monitoring**
   - Check sync logs for errors
   - Monitor the number of properties synced
   - Verify website URLs are correctly captured

## Troubleshooting

### No Properties Found
- Check GA4 credentials are configured correctly
- Verify the service account has access to properties (if using service account authentication)
- If using OAuth2, ensure authorization is complete and tokens are valid
- Ensure the Analytics Admin API is enabled

### Only One Property Synced
- If only one property appears despite having access to many:
  - Verify you're using OAuth2 authentication (not service account)
  - Check OAuth2 authorization status in admin panel
  - Re-authorize OAuth2 if needed

### Sync Errors
- Check the logs for detailed error messages
- Verify database permissions
- Ensure property IDs are valid
- For OAuth2 errors, check token expiration and validity

### Missing Websites
- Some properties may not have web data streams
- Check if the property type supports websites
- Verify data stream permissions
- Website fetching may time out for large property counts

## Example Workflow

### Using Service Account Authentication

1. **Initial Setup with Service Account**
   ```bash
   # Configure Service Account credentials
   python app.py  # Navigate to /admin/ga4-config
   # Select "Service Account" and upload JSON key file
   
   # Run initial sync
   python sync_properties.py --output-json initial_sync.json
   ```

### Using OAuth2 Authentication (Recommended)

1. **Initial Setup with OAuth2**
   ```bash
   # Configure OAuth2 credentials
   python app.py  # Navigate to /admin/ga4-config
   # Select "OAuth2" and enter client ID and secret
   # Click "Authorize with Google" and complete authorization
   
   # Run initial sync (will use OAuth2)
   python sync_properties.py --output-json initial_sync.json
   ```

2. **View Current State**
   ```bash
   python sync_properties.py --summary-only
   ```

3. **Update Specific Property**
   ```bash
   python sync_properties.py --single-property 123456789
   ```

4. **Automated Sync (cron)**
   ```bash
   # Add to crontab
   0 */6 * * * cd /path/to/project && python sync_properties.py >> sync.log 2>&1
   ```