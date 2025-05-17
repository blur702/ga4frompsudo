import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from app.models.base_model import BaseModel

logger = logging.getLogger(__name__)

class User(BaseModel):
    """
    User model for authentication and authorization.
    
    Attributes:
        id: The unique identifier for the user
        email: User's email address (used for login)
        password_hash: Hashed password
        first_name: User's first name
        last_name: User's last name
        roles: List of roles assigned to the user
        is_active: Whether the user account is active
        created_at: When the user was created
        updated_at: When the user was last updated
        last_login: When the user last logged in
    """
    
    @property
    def TABLE_NAME(self):
        return 'users'
    
    def __init__(self, database, id_val=None, email='', password_hash='',
                 first_name='', last_name='', roles=None,
                 is_active=True, created_at=None, updated_at=None, last_login=None):
        """Initialize a new User instance."""
        super().__init__(database, id_val)
        self.email = email
        self.password_hash = password_hash
        self.first_name = first_name
        self.last_name = last_name
        self.roles = roles or ['user']
        self.is_active = is_active
        self.created_at = created_at
        self.updated_at = updated_at
        self.last_login = last_login
    
    def _to_dict(self):
        """
        Convert User instance to a dictionary for database operations.
        Excludes id field which is handled by BaseModel.
        
        Returns:
            Dictionary representation of the user
        """
        # Convert roles list to comma-separated string for DB storage
        roles_str = ','.join(self.roles) if self.roles else 'user'
        
        data = {
            'email': self.email,
            'password_hash': self.password_hash,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'roles': roles_str,
            'is_active': 1 if self.is_active else 0
        }
        
        # Handle datetime fields
        if self.created_at:
            data['created_at'] = self._datetime_to_iso(self.created_at)
        if self.updated_at:
            data['updated_at'] = self._datetime_to_iso(self.updated_at)
        if self.last_login:
            data['last_login'] = self._datetime_to_iso(self.last_login)
            
        return data
    
    @classmethod
    def _from_db_row(cls, row_dict, database_instance):
        """
        Creates a User instance from a database row.
        
        Args:
            row_dict: Dictionary containing row data
            database_instance: Database instance to associate with the model
            
        Returns:
            User instance
        """
        # Parse roles from comma-separated string
        roles = row_dict.get('roles', 'user')
        if isinstance(roles, str):
            roles = roles.split(',')
        
        # Parse datetime fields
        created_at = None
        if row_dict.get('created_at'):
            created_at = datetime.fromisoformat(row_dict['created_at']) if row_dict['created_at'] else None
            
        updated_at = None
        if row_dict.get('updated_at'):
            updated_at = datetime.fromisoformat(row_dict['updated_at']) if row_dict['updated_at'] else None
            
        last_login = None
        if row_dict.get('last_login'):
            last_login = datetime.fromisoformat(row_dict['last_login']) if row_dict['last_login'] else None
        
        # Create and return a new User instance
        return cls(
            database=database_instance,
            id_val=row_dict.get('id'),
            email=row_dict.get('email', ''),
            password_hash=row_dict.get('password_hash', ''),
            first_name=row_dict.get('first_name', ''),
            last_name=row_dict.get('last_name', ''),
            roles=roles,
            is_active=bool(row_dict.get('is_active', 1)),
            created_at=created_at,
            updated_at=updated_at,
            last_login=last_login
        )
    
    def to_dict(self, exclude_sensitive=True):
        """
        Convert User instance to a dictionary for API responses.
        
        Args:
            exclude_sensitive: Whether to exclude sensitive fields like password_hash
            
        Returns:
            Dictionary representation of the user
        """
        data = {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'roles': self.roles,
            'is_active': self.is_active,
            'created_at': self._datetime_to_iso(self.created_at),
            'updated_at': self._datetime_to_iso(self.updated_at),
            'last_login': self._datetime_to_iso(self.last_login)
        }
        
        if not exclude_sensitive:
            data['password_hash'] = self.password_hash
            
        return data
    
    def update_login_timestamp(self):
        """Update the last login timestamp for the user."""
        if not self.id:
            logger.warning("Cannot update login timestamp for user without ID")
            return
            
        self.last_login = datetime.utcnow()
        
        # Use BaseModel's save method which handles updates
        query = f"UPDATE {self.TABLE_NAME} SET last_login = ? WHERE id = ?"
        self.database.execute(query, (self._datetime_to_iso(self.last_login), self.id), commit=True)
        logger.debug(f"Updated last_login for user ID {self.id}")
    
    def has_role(self, role):
        """
        Check if the user has a specific role.
        
        Args:
            role: Role to check for
            
        Returns:
            True if user has the role, False otherwise
        """
        return role in self.roles if self.roles else False
    
    @classmethod
    def find_by_email(cls, database_instance, email):
        """
        Find a user by email address.
        
        Args:
            database_instance: Database instance to use for the query
            email: Email to search for
            
        Returns:
            User instance if found, None otherwise
        """
        # Create a temporary instance to access the TABLE_NAME property
        temp_instance = cls(database_instance)
        
        query = f"SELECT * FROM {temp_instance.TABLE_NAME} WHERE email = ?"
        row_dict = database_instance.execute(query, (email,), fetchone=True)
        
        if not row_dict:
            return None
            
        return cls._from_db_row(row_dict, database_instance)
    
    @classmethod
    def create_tables(cls, database_instance):
        """
        Create the users table if it doesn't exist.
        
        Args:
            database_instance: Database instance to use for creating tables
        """
        query = f"""
        CREATE TABLE IF NOT EXISTS {cls.TABLE_NAME} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            first_name TEXT,
            last_name TEXT,
            roles TEXT DEFAULT 'user',
            is_active INTEGER DEFAULT 1,
            created_at TEXT,
            updated_at TEXT,
            last_login TEXT
        )
        """
        database_instance.execute(query, commit=True)
        logger.info(f"Created {cls.TABLE_NAME} table if it didn't exist")
    
    @property
    def full_name(self):
        """Get the user's full name."""
        return f"{self.first_name} {self.last_name}".strip()