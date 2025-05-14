# 05 - Database Model

This file details the pseudocode for the database connection and management module. This module is fundamental for data persistence in the application.

**Target Application File:** `app/models/database.py`
**Corresponding Test File:** `tests/unit/models/test_database.py` (The LLM should generate tests based on the `testing-pseudocode.md` general principles and specific model test examples.)

## Pseudocode (from `models-pseudocode.md`, refined)

```python
"""
Database connection and management module.
Handles database initialization, connections, basic query execution, and transactions
for an SQLite database.
"""

import sqlite3
import logging # For logging database operations
import threading # For thread-local connections if needed, or managing connections per request

# Get a logger instance for this module
logger = logging.getLogger(__name__)

class Database:
    """
    Manages connections and operations for an SQLite database.
    This class provides methods to connect, initialize the schema,
    execute queries, and handle transactions.
    """

    def __init__(self, db_path):
        """
        Initialize the Database manager.

        Args:
            db_path (str): The path to the SQLite database file.
                           For an in-memory database, use ':memory:'.
        """
        self.db_path = db_path
        # Using thread-local storage for connections can help manage connections
        # in a multi-threaded environment like a Flask app, ensuring each thread
        # uses its own connection if necessary. Or, manage one connection per app context.
        self._local = threading.local()
        logger.info(f"Database manager initialized for database at: {self.db_path}")

    def _get_connection(self):
        """
        Gets the current thread's database connection or creates a new one.
        Enables row factory for dictionary-like row access and foreign key support.

        Returns:
            sqlite3.Connection: An active SQLite database connection.
        """
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            try:
                self._local.connection = sqlite3.connect(self.db_path, check_same_thread=False) # check_same_thread=False for Flask
                self._local.connection.row_factory = sqlite3.Row # Access columns by name
                self._local.connection.execute("PRAGMA foreign_keys = ON;") # Enable foreign key constraints
                logger.debug(f"New SQLite connection established for thread {threading.get_ident()} to {self.db_path}")
            except sqlite3.Error as e:
                logger.error(f"Failed to connect to database at {self.db_path}: {e}", exc_info=True)
                raise
        return self._local.connection

    def close_connection(self, exc=None): # pylint: disable=unused-argument
        """
        Closes the current thread's database connection.
        Intended to be used with Flask's app.teardown_appcontext.

        Args:
            exc (Exception, optional): Exception information if an error occurred.
        """
        connection = getattr(self._local, 'connection', None)
        if connection is not None:
            connection.close()
            self._local.connection = None
            logger.debug(f"SQLite connection closed for thread {threading.get_ident()}.")

    def initialize(self):
        """
        Initializes the database schema by creating necessary tables if they don't already exist.
        This method should define the structure of all tables required by the application.

        Returns:
            bool: True if initialization was successful, False otherwise.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            logger.info("Initializing database schema...")

            # Properties Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS properties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                property_id TEXT UNIQUE NOT NULL,
                property_name TEXT,
                account_id TEXT,
                create_time TEXT, -- ISO 8601 format
                update_time TEXT  -- ISO 8601 format
            );
            """)
            logger.debug("Table 'properties' ensured.")

            # Websites Table (associated with Properties)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS websites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                website_id TEXT UNIQUE NOT NULL, -- Could be GA4 stream ID
                property_db_id INTEGER NOT NULL, -- Foreign key to properties.id
                website_url TEXT,
                create_time TEXT, -- ISO 8601 format
                update_time TEXT, -- ISO 8601 format
                FOREIGN KEY (property_db_id) REFERENCES properties (id) ON DELETE CASCADE
            );
            """)
            logger.debug("Table 'websites' ensured.")

            # Reports Table (metadata for generated reports)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_name TEXT NOT NULL,
                report_type TEXT NOT NULL, -- e.g., 'traffic_analysis', 'engagement'
                parameters TEXT,           -- JSON string of parameters used for generation
                create_time TEXT NOT NULL, -- ISO 8601 format
                status TEXT,               -- e.g., 'pending', 'generating', 'completed', 'failed'
                file_path TEXT             -- Path to the generated report file if applicable
            );
            """)
            logger.debug("Table 'reports' ensured.")

            # Report Data Table (stores data points for reports - flexible design)
            # This table might need a more complex structure or be split depending on needs.
            # Storing as JSON blobs or EAV might be options for flexibility.
            # For structured data, consider specific columns.
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS report_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_db_id INTEGER NOT NULL,      -- Foreign key to reports.id
                property_ga4_id TEXT,               -- GA4 Property ID this data pertains to
                metric_name TEXT NOT NULL,
                metric_value TEXT,                  -- Store as TEXT for flexibility, convert on read
                dimension_name TEXT,
                dimension_value TEXT,
                data_date TEXT,                     -- Date for which this data point is relevant (YYYY-MM-DD)
                timestamp TEXT NOT NULL,            -- When this record was saved (ISO 8601)
                FOREIGN KEY (report_db_id) REFERENCES reports (id) ON DELETE CASCADE
            );
            """)
            logger.debug("Table 'report_data' ensured.")

            # Add more table definitions here as needed (e.g., users, settings)

            conn.commit()
            logger.info("Database schema initialization successful.")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error initializing database schema: {e}", exc_info=True)
            conn.rollback() # Rollback changes if an error occurs
            return False
        # No finally block to close connection, as _get_connection manages it per thread/request lifecycle.

    def execute(self, query, params=None, commit=False, fetchone=False, fetchall=False):
        """
        Executes a given SQL query.

        Args:
            query (str): The SQL query to execute.
            params (tuple, optional): A tuple of parameters to substitute into the query. Defaults to None.
            commit (bool, optional): Whether to commit the transaction after execution. Defaults to False.
            fetchone (bool, optional): Whether to fetch one row after execution. Defaults to False.
            fetchall (bool, optional): Whether to fetch all rows after execution. Defaults to False.

        Returns:
            sqlite3.Cursor or dict or list or None:
                - Cursor object if no fetch option is specified.
                - A single dictionary (row) if fetchone is True.
                - A list of dictionaries (rows) if fetchall is True.
                - None if an error occurs or if fetchone finds no row.

        Raises:
            sqlite3.Error: If an error occurs during query execution.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            logger.debug(f"Executing query: {query} with params: {params}")
            cursor.execute(query, params or ())

            if commit:
                conn.commit()
                logger.debug("Query committed.")

            if fetchone:
                row = cursor.fetchone()
                # sqlite3.Row can be converted to dict: dict(row) if row else None
                return dict(row) if row else None
            if fetchall:
                rows = cursor.fetchall()
                # Convert list of sqlite3.Row to list of dicts
                return [dict(row) for row in rows]

            return cursor # Return cursor for more complex operations if needed (e.g., lastrowid)
        except sqlite3.Error as e:
            logger.error(f"Database query execution failed: {query} - {params} - {e}", exc_info=True)
            if commit: # Only rollback if we intended to commit but failed
                conn.rollback()
            raise # Re-raise the exception to be handled by the caller

    def transaction(self):
        """
        Provides a context manager for database transactions.
        Example usage:
            with db.transaction():
                db.execute(...)
                db.execute(...)
        If an exception occurs within the 'with' block, the transaction is rolled back.
        Otherwise, it's committed upon exiting the block.
        """
        return TransactionContext(self._get_connection())


class TransactionContext:
    """
    A context manager for SQLite transactions.
    Ensures that transactions are properly committed or rolled back.
    """
    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        """Begins a new transaction."""
        # For SQLite, 'BEGIN' is often implicit with DML statements if not in autocommit mode.
        # Explicitly: self.connection.execute("BEGIN TRANSACTION;")
        # However, sqlite3 module handles this by default; commit/rollback manage it.
        logger.debug("Entering transaction context.")
        return self # The context manager itself can be returned if needed

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exits the transaction context.
        Commits if no exception occurred, otherwise rolls back.
        """
        if exc_type is None:
            self.connection.commit()
            logger.debug("Transaction committed successfully.")
        else:
            self.connection.rollback()
            logger.warning(f"Transaction rolled back due to exception: {exc_type.__name__} {exc_val}", exc_info=(exc_type, exc_val, exc_tb))
        # Do not suppress the exception, let it propagate
        return False # Returning False re-raises the exception if one occurred
```
