# 04 - Testing Framework Setup

This file outlines the setup for the testing framework, including the main test configuration file (`tests/conftest.py`) and the overall testing strategy. This is crucial for enabling Test-Driven Development (TDD) from the outset.

## 1. Test Configuration and Fixtures

Target file: `tests/conftest.py`

### Pseudocode (from `testing-pseudocode.md`, refined in previous turns)

```python
"""
Test configuration and fixtures for pytest.
This file provides common fixtures available to all tests.
Fixtures defined here are automatically discovered by pytest.
"""

import os
import tempfile
import pytest
import shutil # For cleaning up directories if needed
import logging # For logging within fixtures if necessary
from app import create_app # Main application factory

@pytest.fixture(scope='session')
def app():
    """
    Create and configure a new Flask app instance for the entire test session.
    Uses 'testing' configuration. The TestingConfig should handle specifics
    like an in-memory database or a unique temporary file-based database.
    """
    # The TestingConfig should set DATABASE_PATH appropriately (e.g., ':memory:'
    # or a unique temporary file path which it would also be responsible for cleaning up if needed).
    # It also sets a temporary path for the SECURITY key.
    test_app = create_app(config_name='testing')
    test_app.logger.info("Test application instance created for session.")

    # The application context is pushed so that any operations requiring it
    # (like database initialization within create_app or extensions) work correctly.
    with test_app.app_context():
        # Assuming create_app and its init_extensions function fully handle
        # database setup based on the 'testing' configuration.
        # If specific schema creation or initial data is needed for all tests
        # across the session, it could be done here.
        # For example, if app.database.initialize() needs to be explicitly called again
        # or if there's a special setup for test DBs:
        # if hasattr(test_app, 'database'):
        #     test_app.database.initialize() # Ensure tables are created.
        pass

    yield test_app # Provide the app instance to the test session

    # Teardown: Executed after all tests in the session are done.
    # Clean up the temporary encryption key created by TestingConfig.
    security_config = test_app.config.get('SECURITY', {})
    test_key_path = security_config.get('key_path')

    if test_key_path and os.path.exists(test_key_path) and "ga4dash_test_key" in test_key_path: # Safety check
        try:
            os.unlink(test_key_path)
            test_app.logger.info(f"Cleaned up session test encryption key: {test_key_path}")
        except OSError as e:
            test_app.logger.error(f"Error cleaning up session test key {test_key_path}: {e}")

    # If TestingConfig used a file-based DB and created a temp directory itself,
    # it should ideally clean it up. If conftest.py created it, cleanup here:
    # e.g., if db_path = os.path.join(temp_dir, "test_app.db") was used
    # if 'temp_dir_for_db' in locals() and os.path.exists(temp_dir_for_db):
    #     shutil.rmtree(temp_dir_for_db)
    #     test_app.logger.info(f"Cleaned up temporary test DB directory: {temp_dir_for_db}")
    test_app.logger.info("Test application teardown complete for session.")


@pytest.fixture(scope='function')
def client(app):
    """
    Create a Flask test client for the app.
    A new client is created for each test function, ensuring test isolation for requests.
    The client operates within an application context.

    Args:
        app (Flask): The session-scoped Flask application fixture.

    Returns:
        FlaskClient: The Flask test client.
    """
    # app.test_client() creates a client that can make requests to the application
    # without needing a running web server.
    return app.test_client()


@pytest.fixture(scope='function')
def runner(app):
    """
    Provides a Flask CLI test runner.
    Useful for testing custom CLI commands registered with the application.

    Args:
        app (Flask): The session-scoped Flask application fixture.
    Returns:
        FlaskCliRunner: The Flask CLI test runner.
    """
    return app.test_cli_runner()


@pytest.fixture(scope='function')
def db(app):
    """
    Provides the application's database instance for a test function.
    It ensures operations are within an app context.
    This fixture is suitable for tests that need to interact directly with the database.
    If using an in-memory SQLite database (as per TestingConfig), each test effectively
    gets a clean slate if the connection is re-established or tables are re-created.
    If the database connection is persistent across the session for an in-memory DB,
    tests should clean up any data they create or this fixture should handle it.
    However, app.database.initialize() in create_app should handle table creation.

    Args:
        app (Flask): The session-scoped Flask application fixture.

    Yields:
        Database: The application's database instance, ready for use.
    """
    with app.app_context():
        # Ensure tables are created (idempotent operation from Database.initialize)
        # app.database.initialize() # Usually already done by create_app

        # For function-scoped DB interactions where data needs to be clean:
        # One strategy is to clear tables before each test, or use transactions and rollback.
        # Example:
        # app.database.clear_all_tables() # Implement this method in Database class
        # app.database.initialize() # Recreate schema

        yield app.database

        # After test, clean up data if necessary (if not using transactions or full DB recreation)
        # Example:
        # app.database.clear_all_tables()


# Fixtures for providing initialized service instances within an app context.
# These are function-scoped to ensure they are fetched fresh for each test,
# reflecting any app state that might be relevant (though ideally services are stateless).

@pytest.fixture(scope='function')
def auth_service(app):
    """Get the Authentication service instance from the current app context."""
    with app.app_context(): # Ensure an app context is active
        return app.auth_service

@pytest.fixture(scope='function')
def ga4_service_fixture(app): # Renamed to avoid potential name clashes
    """Get the GA4 service instance from the current app context."""
    with app.app_context():
        return app.ga4_service

@pytest.fixture(scope='function')
def plugin_service_fixture(app): # Renamed
    """Get the Plugin service instance from the current app context."""
    with app.app_context():
        return app.plugin_service

@pytest.fixture(scope='function')
def report_service_fixture(app): # Renamed
    """Get the Report service instance from the current app context."""
    with app.app_context():
        return app.report_service

@pytest.fixture(scope='function')
def security_service_fixture(app): # Renamed
    """Get the Security service instance from the current app context."""
    with app.app_context():
        return app.security_service

@pytest.fixture(scope='session')
def mock_ga4_data():
    """
    Provides a consistent set of mock/sample data for testing purposes.
    This can simulate responses from GA4Service, data for views, or inputs for processing.
    Being session-scoped, it's created once per test session.

    Returns:
        dict: A dictionary containing various mock GA4-related data structures.
    """
    return {
        "properties_list_api_response": [ # Simulates GA4Service.get_properties() output
            {"property_id": "123", "property_name": "Alpha Analytics Property", "account_id": "acc_alpha_001", "create_time": "2023-01-15T10:00:00Z", "update_time": "2023-01-16T11:00:00Z"},
            {"property_id": "456", "property_name": "Beta Web Insights", "account_id": "acc_beta_002", "create_time": "2023-02-20T14:30:00Z", "update_time": "2023-02-21T15:00:00Z"}
        ],
        "websites_list_api_response": [ # Simulates GA4Service.get_websites() output for a property
            {"website_id": "web_stream_alpha_01", "property_id": "123", "website_url": "[https://alpha.example.gov](https://alpha.example.gov)", "create_time": "2023-01-15T10:05:00Z", "update_time": "2023-01-15T10:05:00Z"}
        ],
        "dashboard_view_data": { # Example data structure a controller might pass to a dashboard template
            "total_users": 2500, "total_sessions": 3200, "total_pageviews": 12800,
            "average_session_duration_seconds": 185.5,
            "pageviews_per_session": 4.0,
            "bounce_rate_percentage": 22.5, # As percentage
            "daily_traffic_data": { # For charts
                "2023-05-01": {"users": 150, "sessions": 180, "pageviews": 720},
                "2023-05-02": {"users": 165, "sessions": 190, "pageviews": 780},
                # ... more dates
            }
        },
        "ga4_raw_run_report_response": { # Simulates a raw response from GA4 Data API client's run_report
            "dimensionHeaders": [{'name': 'date'}, {'name': 'newVsReturningUser'}],
            "metricHeaders": [{'name': 'activeUsers'}, {'name': 'sessions'}, {'name': 'screenPageViews'}],
            "rows": [
                {'dimensionValues': [{'value': '20230501'}, {'value': 'new'}], 'metricValues': [{'value': '80'}, {'value': '90'}, {'value': '350'}]},
                {'dimensionValues': [{'value': '20230501'}, {'value': 'returning'}], 'metricValues': [{'value': '70'}, {'value': '90'}, {'value': '370'}]},
                {'dimensionValues': [{'value': '20230502'}, {'value': 'new'}], 'metricValues': [{'value': '90'}, {'value': '100'}, {'value': '400'}]},
                {'dimensionValues': [{'value': '20230502'}, {'value': 'returning'}], 'metricValues': [{'value': '75'}, {'value': '90'}, {'value': '380'}]}
            ],
            "rowCount": 4,
            "metadata": {"currencyCode": "USD", "timeZone": "America/New_York"},
            "kind": "analyticsData#runReport"
        }
    }
```
