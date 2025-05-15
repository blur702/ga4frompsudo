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
    table_name = 'users'
    
    def __init__(self, id: Optional[int] = None, email: str = '', password_hash: str = '',
                 first_name: str = '', last_name: str = '', roles: List[str] = None,
                 is_active: bool = True, created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None, last_login: Optional[datetime] = None):
        """Initialize a new User instance."""
        super().__init__(id, created_at, updated_at)
        self.email = email
        self.password_hash = password_hash
        self.first_name = first_name
        self.last_name = last_name
        self.roles = roles or ['user']
        self.is_active = is_active
        self.last_login = last_login
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """
        Create a User instance from a dictionary.
        
        Args:
            data: Dictionary containing user data
            
        Returns:
            User instance
        """
        roles = data.get('roles', ['user'])
        if isinstance(roles, str):
            roles = roles.split(',')
            
        return cls(
            id=data.get('id'),
            email=data.get('email', ''),
            password_hash=data.get('password_hash', ''),
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            roles=roles,
            is_active=data.get('is_active', True),
            created_at=cls._parse_datetime(data.get('created_at')),
            updated_at=cls._parse_datetime(data.get('updated_at')),
            last_login=cls._parse_datetime(data.get('last_login'))
        )
    
    def to_dict(self, exclude_sensitive: bool = True) -> Dict[str, Any]:
        """
        Convert User instance to a dictionary.
        
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
            'roles': ','.join(self.roles) if self.roles else '',
            'is_active': self.is_active,
            'created_at': self._format_datetime(self.created_at),
            'updated_at': self._format_datetime(self.updated_at),
            'last_login': self._format_datetime(self.last_login)
        }
        
        if not exclude_sensitive:
            data['password_hash'] = self.password_hash
            
        return data
    
    def save(self) -> int:
        """
        Save the user to the database.
        
        Returns:
            User ID
        """
        data = self.to_dict(exclude_sensitive=False)
        
        if self.id:
            # Update existing user
            data.pop('id')
            data['updated_at'] = self._format_datetime(datetime.utcnow())
            result = self.update(self.id, data)
            logger.info(f"Updated user with ID {self.id}")
            return self.id
        else:
            # Insert new user
            data.pop('id', None)
            data['created_at'] = self._format_datetime(datetime.utcnow())
            data['updated_at'] = data['created_at']
            self.id = self.insert(data)
            logger.info(f"Created new user with ID {self.id}")
            return self.id
    
    def has_role(self, role: str) -> bool:
        """
        Check if the user has a specific role.
        
        Args:
            role: Role to check for
            
        Returns:
            True if user has the role, False otherwise
        """
        return role in self.roles if self.roles else False
    
    def update_login_timestamp(self) -> None:
        """Update the last login timestamp for the user."""
        self.last_login = datetime.utcnow()
        self.update(self.id, {'last_login': self._format_datetime(self.last_login)})
        logger.debug(f"Updated last_login for user ID {self.id}")
    
    @classmethod
    def find_by_email(cls, email: str) -> Optional['User']:
        """
        Find a user by email address.
        
        Args:
            email: Email to search for
            
        Returns:
            User instance if found, None otherwise
        """
        query = f"SELECT * FROM {cls.table_name} WHERE email = ?"
        result = cls.execute_query(query, (email,))
        
        if not result:
            return None
            
        return cls.from_dict(result[0])
    
    @classmethod
    def create_tables(cls) -> None:
        """Create the users table if it doesn't exist."""
        query = f"""
        CREATE TABLE IF NOT EXISTS {cls.table_name} (
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
        cls.execute_query(query)
        logger.info(f"Created {cls.table_name} table if it didn't exist")
    
    @property
    def full_name(self) -> str:
        """Get the user's full name."""
        return f"{self.first_name} {self.last_name}".strip()