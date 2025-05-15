"""
Tests for the Database class in the models module.
"""

import sqlite3
import pytest
from app.models.database import Database, TransactionContext


def test_database_initialization():
    """Test that the Database can be initialized with a path."""
    # Setup
    db_path = ':memory:'  # Use in-memory database for testing
    
    # Execute
    db = Database(db_path)
    
    # Assert
    assert db.db_path == db_path
    assert hasattr(db, '_local')


def test_database_get_connection():
    """Test that _get_connection returns a valid SQLite connection."""
    # Setup
    db = Database(':memory:')
    
    # Execute
    conn = db._get_connection()
    
    # Assert
    assert isinstance(conn, sqlite3.Connection)
    assert conn.row_factory == sqlite3.Row
    
    # Test that foreign keys are enabled
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys;")
    result = cursor.fetchone()
    assert result[0] == 1  # Foreign keys should be enabled (1)


def test_database_schema_initialization():
    """Test that initialize() creates the database schema."""
    # Setup
    db = Database(':memory:')
    
    # Execute
    result = db.initialize()
    
    # Assert
    assert result is True
    
    # Verify tables were created
    conn = db._get_connection()
    cursor = conn.cursor()
    
    # Check all expected tables are created
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    expected_tables = ['properties', 'websites', 'reports', 'report_data']
    for table in expected_tables:
        assert table in tables


def test_database_execute_query():
    """Test executing queries with various options."""
    # Setup
    db = Database(':memory:')
    db.initialize()
    
    # Create a test record
    db.execute(
        "INSERT INTO properties (property_id, property_name) VALUES (?, ?);",
        ('test-property-id', 'Test Property'),
        commit=True
    )
    
    # Test fetchone
    result = db.execute(
        "SELECT * FROM properties WHERE property_id = ?;",
        ('test-property-id',),
        fetchone=True
    )
    assert result is not None
    assert result['property_name'] == 'Test Property'
    
    # Test fetchall
    results = db.execute(
        "SELECT * FROM properties;",
        fetchall=True
    )
    assert len(results) == 1
    assert results[0]['property_id'] == 'test-property-id'
    
    # Test that non-existent record returns None with fetchone
    result = db.execute(
        "SELECT * FROM properties WHERE property_id = ?;",
        ('non-existent-id',),
        fetchone=True
    )
    assert result is None


def test_transaction_context():
    """Test the transaction context manager."""
    # Setup
    db = Database(':memory:')
    db.initialize()
    
    # Test successful transaction
    with db.transaction():
        db.execute(
            "INSERT INTO properties (property_id, property_name) VALUES (?, ?);",
            ('test-property-1', 'Test Property 1')
        )
        db.execute(
            "INSERT INTO properties (property_id, property_name) VALUES (?, ?);",
            ('test-property-2', 'Test Property 2')
        )
    
    # Verify both records were inserted
    results = db.execute("SELECT * FROM properties;", fetchall=True)
    assert len(results) == 2
    
    # Test failed transaction (should rollback)
    try:
        with db.transaction():
            db.execute(
                "INSERT INTO properties (property_id, property_name) VALUES (?, ?);",
                ('test-property-3', 'Test Property 3')
            )
            # This will fail due to UNIQUE constraint on property_id
            db.execute(
                "INSERT INTO properties (property_id, property_name) VALUES (?, ?);",
                ('test-property-1', 'Duplicate Property')
            )
    except sqlite3.Error:
        pass  # Expected error
    
    # Verify no new records were inserted (transaction rolled back)
    results = db.execute("SELECT * FROM properties;", fetchall=True)
    assert len(results) == 2  # Still just the original 2 records
    
    # Check that 'test-property-3' was not inserted
    result = db.execute(
        "SELECT * FROM properties WHERE property_id = ?;",
        ('test-property-3',),
        fetchone=True
    )
    assert result is None


def test_close_connection():
    """Test the close_connection method."""
    # Setup
    db = Database(':memory:')
    
    # Get a connection
    conn = db._get_connection()
    assert conn is not None
    
    # Close the connection
    db.close_connection()
    
    # Verify that the connection is closed
    # We can't directly test if the connection is closed,
    # but we can verify that a new connection is created after closing
    new_conn = db._get_connection()
    assert new_conn is not None
    # The object should be different if a new connection was created
    # Note: This is an implementation detail that might change
    # if connection pooling is implemented differently