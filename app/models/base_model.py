"""
Base model with common database interaction functionalities.
All specific model classes (e.g., Property, Website) in the application
are expected to inherit from this BaseModel to gain common CRUD operations
and other shared database logic.
"""

import logging
from abc import ABC, abstractmethod

# Get a logger instance for this module
logger = logging.getLogger(__name__)

class BaseModel(ABC):
    """
    Abstract base class for all database models.

    Provides common methods for database operations such as save, delete,
    and find. Subclasses must implement specific table interactions
    or override these methods if specialized behavior is needed.

    Attributes:
        database (Database): An instance of the Database class for executing queries.
        id (int, optional): The primary key of the model instance in the database.
                        It's typically None for new instances until saved.
    """

    # Subclasses should define their table name as a class attribute.
    # TABLE_NAME = 'table_name' # Example: 'properties', 'websites', etc.

    def __init__(self, database, id_val=None):
        """
        Initializes the base model with a database instance and an optional ID.

        Args:
            database (Database): An instance of the Database class from `app.models.database`.
            id_val (int, optional): The ID of the model if it's an existing record.
                                   Defaults to None for new records.
        """
        if database is None:
            logger.error("Database instance cannot be None for BaseModel.")
            raise ValueError("Database instance is required for BaseModel.")
        self.database = database
        self.id = id_val  # Corresponds to the 'id' INTEGER PRIMARY KEY AUTOINCREMENT column

    # Subclasses should define their table name as a class attribute.
    # Example: TABLE_NAME = 'properties'

    @abstractmethod
    def _to_dict(self):
        """
        Converts the model's attributes to a dictionary suitable for database insertion or update.
        Excludes 'id' if it's None (for inserts) and internal attributes like 'database'.
        This method MUST be implemented by subclasses.

        Returns:
            dict: A dictionary representation of the model's savable fields.
        """
        pass

    @classmethod
    @abstractmethod
    def _from_db_row(cls, row_dict, database_instance):
        """
        Creates an instance of the model from a database row (dictionary).
        This method MUST be implemented by subclasses.

        Args:
            row_dict (dict): A dictionary representing a row from the database.
            database_instance (Database): The database instance to associate with the new model instance.

        Returns:
            An instance of the subclass model.
        """
        pass

    def save(self):
        """
        Saves the current model instance to the database.
        If the instance has an ID, it attempts an UPDATE.
        Otherwise, it performs an INSERT.

        The specific fields to save are determined by the `_to_dict()` method
        implemented in the subclass. The `id` is automatically handled.

        Returns:
            int or None: The ID of the saved record (newly inserted or existing).
                         Returns None if the save operation failed.
        """
        data_to_save = self._to_dict()  # Get fields from subclass
        if not data_to_save:
            logger.warning(f"No data to save for model {self.__class__.__name__}. _to_dict() returned empty.")
            return None

        try:
            if self.id is not None:  # Existing record, perform UPDATE
                logger.debug(f"Updating record ID {self.id} in table {self.TABLE_NAME} with data: {data_to_save}")
                # Construct SET clause: "field1 = ?, field2 = ?"
                set_clause = ", ".join([f"{key} = ?" for key in data_to_save.keys()])
                values = list(data_to_save.values()) + [self.id]
                query = f"UPDATE {self.TABLE_NAME} SET {set_clause} WHERE id = ?"
                cursor = self.database.execute(query, tuple(values), commit=True)
                logger.info(f"Record ID {self.id} updated successfully in {self.TABLE_NAME}.")
                return self.id
            else:  # New record, perform INSERT
                logger.debug(f"Inserting new record into table {self.TABLE_NAME} with data: {data_to_save}")
                columns = ", ".join(data_to_save.keys())
                placeholders = ", ".join(["?"] * len(data_to_save))
                values = tuple(data_to_save.values())
                query = f"INSERT INTO {self.TABLE_NAME} ({columns}) VALUES ({placeholders})"

                cursor = self.database.execute(query, values, commit=True)
                self.id = cursor.lastrowid  # Update the instance with the new ID
                logger.info(f"New record inserted into {self.TABLE_NAME} with ID: {self.id}.")
                return self.id
        except Exception as e:  # Catch more specific sqlite3.Error if possible
            logger.error(f"Error saving record to table {self.TABLE_NAME}: {e}", exc_info=True)
            return None

    def delete(self):
        """
        Deletes the current model instance from the database based on its ID.
        If the instance does not have an ID (i.e., it hasn't been saved yet),
        this method does nothing.

        Returns:
            bool: True if the deletion was successful, False otherwise.
        """
        if self.id is None:
            logger.warning(f"Attempted to delete a record from {self.TABLE_NAME} without an ID. Operation aborted.")
            return False
        try:
            logger.debug(f"Deleting record ID {self.id} from table {self.TABLE_NAME}.")
            query = f"DELETE FROM {self.TABLE_NAME} WHERE id = ?"
            cursor = self.database.execute(query, (self.id,), commit=True)
            # SQLite Cursor doesn't have rowcount property that reliably tells affected rows
            # We'll assume success if no exception was raised
            logger.info(f"Record ID {self.id} deleted successfully from {self.TABLE_NAME}.")
            self.id = None  # Clear ID after deletion
            return True
        except Exception as e:  # Catch more specific sqlite3.Error if possible
            logger.error(f"Error deleting record ID {self.id} from table {self.TABLE_NAME}: {e}", exc_info=True)
            return False

    @classmethod
    def find_by_id(cls, database_instance, record_id):
        """
        Finds a record by its primary key (ID) in the model's table.

        Args:
            database_instance (Database): An instance of the Database class.
            record_id (int): The ID of the record to find.

        Returns:
            An instance of the model subclass if found, otherwise None.
        """
        try:
            logger.debug(f"Finding record by ID {record_id} in table {cls.TABLE_NAME}.")
            query = f"SELECT * FROM {cls.TABLE_NAME} WHERE id = ?"
            row_dict = database_instance.execute(query, (record_id,), fetchone=True)
            if row_dict:
                return cls._from_db_row(row_dict, database_instance)  # Use subclass's factory method
            return None
        except Exception as e:  # Catch more specific sqlite3.Error if possible
            logger.error(f"Error finding record by ID {record_id} in table {cls.TABLE_NAME}: {e}", exc_info=True)
            return None

    @classmethod
    def get_by_field(cls, database_instance, field_name, field_value):
        """
        Finds a model instance by a specific field.

        Args:
            database_instance (Database): The database instance to use.
            field_name (str): The name of the field to search by.
            field_value: The value to search for.

        Returns:
            An instance of the subclass model or None if not found.
        """
        query = f"SELECT * FROM {cls.TABLE_NAME} WHERE {field_name} = ?"
        try:
            logger.debug(f"Finding record by {field_name}={field_value} in table {cls.TABLE_NAME}.")
            row = database_instance.execute(query, (field_value,), fetchone=True)
            if row:
                return cls._from_db_row(row, database_instance)
            return None
        except Exception as e:
            logger.error(f"Error finding record by {field_name}={field_value} in table {cls.TABLE_NAME}: {e}", exc_info=True)
            return None
    
    @classmethod
    def find_all(cls, database_instance, filters=None, order_by=None, limit=None, offset=None):
        """
        Finds all records in the model's table, with optional filters, ordering, and pagination.

        Args:
            database_instance (Database): An instance of the Database class.
            filters (dict, optional): A dictionary of field-value pairs to filter by (e.g., {'name': 'Test'}).
                                      Currently supports exact matches with AND conditions.
            order_by (str, optional): A string specifying the ordering (e.g., "name ASC", "create_time DESC").
            limit (int, optional): The maximum number of records to return.
            offset (int, optional): The number of records to skip (for pagination).

        Returns:
            list: A list of model subclass instances, or an empty list if no records match or an error occurs.
        """
        query = f"SELECT * FROM {cls.TABLE_NAME}"
        params = []

        if filters:
            # Simple AND filter for now. For complex queries, consider a query builder.
            # WARNING: Ensure filter keys are actual column names to prevent SQL injection if not careful,
            # though parameterization helps. Best to validate keys against known columns.
            # For this example, assuming keys are safe.
            conditions = []
            for key, value in filters.items():
                conditions.append(f"{key} = ?")  # Basic equality
                # Ensure value is properly converted to a compatible type for SQLite
                # SQLite accepts: None, int, float, str, and bytes
                params.append(value)  # SQLite driver handles basic Python types properly
            if conditions:
                query += " WHERE " + " AND ".join(conditions)

        if order_by:
            # Basic ORDER BY. Be cautious with user-supplied `order_by` strings to prevent SQL injection.
            # It's safer to validate `order_by` against a list of allowed columns and directions.
            # For this example, assuming it's safe or internally generated.
            query += f" ORDER BY {order_by}"  # This part is not parameterized, be careful

        if limit is not None:
            query += " LIMIT ?"
            # Ensure limit is an integer
            params.append(int(limit) if limit is not None else None)

        if offset is not None:
            if limit is None:  # SQLite requires LIMIT with OFFSET
                query += " LIMIT -1"  # Effectively no limit, but required by SQLite for OFFSET
            query += " OFFSET ?"
            # Ensure offset is an integer
            params.append(int(offset) if offset is not None else None)

        try:
            logger.debug(f"Finding all records in table {cls.TABLE_NAME} with query: {query}, params: {params}")
            rows = database_instance.execute(query, tuple(params), fetchall=True)
            if rows:
                return [cls._from_db_row(row_dict, database_instance) for row_dict in rows]
            return []
        except Exception as e:  # Catch more specific sqlite3.Error if possible
            logger.error(f"Error finding all records in table {cls.TABLE_NAME}: {e}", exc_info=True)
            return []

    # Helper for subclasses to manage datetime and date fields consistently
    def _datetime_to_iso(self, dt_obj):
        """
        Formats a datetime object to an ISO 8601 string for database storage.
        If dt_obj is already a string, returns it as is.
        """
        if dt_obj is None:
            return None
        if isinstance(dt_obj, str):
            return dt_obj
        return dt_obj.isoformat()

    def _iso_to_datetime(self, dt_str):
        """Parses an ISO 8601 string from the database into a datetime object."""
        if dt_str:
            from datetime import datetime  # Local import
            try:
                # Handle 'Z' timezone designator by converting to +00:00 which fromisoformat understands
                dt_str_normalized = dt_str.replace('Z', '+00:00') if dt_str.endswith('Z') else dt_str
                return datetime.fromisoformat(dt_str_normalized)
            except ValueError:
                logger.warning(f"Could not parse datetime string '{dt_str}' from DB for {self.__class__.__name__} ID {self.id}")
                return None  # Or handle error as appropriate
        return None
        
    def _date_to_iso(self, date_obj):
        """Formats a date object to an ISO 8601 date string (YYYY-MM-DD) for database storage."""
        if date_obj:
            return date_obj.isoformat()
        return None
        
    def _iso_to_date(self, date_str):
        """Parses an ISO 8601 date string (YYYY-MM-DD) from the database into a date object."""
        if date_str:
            from datetime import datetime  # Local import
            try:
                return datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                logger.warning(f"Could not parse date string '{date_str}' from DB for {self.__class__.__name__} ID {self.id}")
                return None  # Or handle error as appropriate
        return None