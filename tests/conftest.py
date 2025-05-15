"""
Test configuration for the GA4 Analytics Dashboard application.
Contains pytest fixtures for use in tests.
"""

import os
import pytest
from flask import Flask
from app import create_app
from app.models.database import Database

@pytest.fixture
def app():
    """Create and configure a Flask application for testing."""
    app = create_app('testing')
    # Establish application context
    with app.app_context():
        yield app


@pytest.fixture
def client(app):
    """Create a test client for the application."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create a test CLI runner for the application."""
    return app.test_cli_runner()


@pytest.fixture
def db():
    """Create a test database instance."""
    # Use in-memory database for testing
    database = Database(':memory:')
    database.initialize()
    return database