"""
Website Model.
Represents a website (often a web data stream in GA4) linked to a GA4 Property.
"""

import logging
import datetime
from typing import Optional, List, TYPE_CHECKING  # For type hinting
from .base_model import BaseModel

# For type hinting related models to avoid circular imports at runtime
if TYPE_CHECKING:
    from .property import Property  # pylint: disable=cyclic-import
    from .database import Database  # For type hint of database_instance

logger = logging.getLogger(__name__)

class Website(BaseModel):
    """
    Represents a website or web data stream associated with a GA4 Property.

    This class stores details about a website, such as its GA4 stream ID (referred to
    as website_id here), the URL, and timestamps. It links back to a `Property`
    instance via `property_db_id`. It inherits common database operations
    from `BaseModel`.

    Attributes:
        website_id (str): The unique identifier for the GA4 web data stream
                          (e.g., 'properties/123/dataStreams/456'). This is treated as the website's unique ID.
        property_db_id (int): The internal database ID of the `Property` this website belongs to. This is a foreign key.
        website_url (Optional[str]): The display URL of the website.
        create_time (Optional[datetime.datetime]): The timestamp when the data stream was created in GA4.
        update_time (Optional[datetime.datetime]): The timestamp when the data stream was last updated in GA4.
        # `id` (internal DB primary key for this website record) and `database` attributes are inherited from BaseModel.
    """

    @property
    def TABLE_NAME(self) -> str:
        """Returns the database table name used for storing Website records."""
        return 'websites'  # As defined in Database.initialize_schema()

    def __init__(self, database: 'Database',
                 website_id: str,
                 property_db_id: int,
                 website_url: Optional[str] = None,
                 create_time: Optional[datetime.datetime] = None,
                 update_time: Optional[datetime.datetime] = None,
                 id_val: Optional[int] = None):
        """
        Initializes a new instance of the Website model.

        Args:
            database (Database): The database instance for data operations.
            website_id (str): The unique GA4 Data Stream ID for this website. Mandatory.
            property_db_id (int): The internal database ID of the parent Property. Mandatory.
            website_url (Optional[str]): The display URL of the website.
            create_time (Optional[datetime.datetime]): Website/Data Stream creation timestamp.
                                                       If str, should be ISO 8601 format.
            update_time (Optional[datetime.datetime]): Website/Data Stream last update timestamp.
                                                       If str, should be ISO 8601 format.
            id_val (Optional[int]): The internal database ID if this website record already exists.

        Raises:
            ValueError: If `website_id` or `property_db_id` is None or invalid.
        """
        super().__init__(database, id_val)
        if not website_id:
            logger.error("Attempted to initialize Website model without a 'website_id'.")
            raise ValueError("GA4 Data Stream ID (website_id) is mandatory and cannot be empty.")
        if property_db_id is None:  # property_db_id can be 0 if that's a valid ID, so check for None
            logger.error("Attempted to initialize Website model without a 'property_db_id'.")
            raise ValueError("Parent Property database ID (property_db_id) is mandatory.")

        self.website_id: str = website_id
        self.property_db_id: int = property_db_id
        self.website_url: Optional[str] = website_url

        # Handle datetime conversion if strings are passed
        self.create_time = self._iso_to_datetime(create_time) if isinstance(create_time, str) else create_time
        self.update_time = self._iso_to_datetime(update_time) if isinstance(update_time, str) else update_time

    def _to_dict(self) -> dict:
        """
        Serializes the Website model's attributes to a dictionary for database storage.
        Datetime objects are converted to ISO 8601 string format.

        Returns:
            dict: A dictionary representation of the Website instance's fields.
        """
        return {
            'website_id': self.website_id,
            'property_db_id': self.property_db_id,
            'website_url': self.website_url,
            'create_time': self._datetime_to_iso(self.create_time),
            'update_time': self._datetime_to_iso(self.update_time)
        }

    @classmethod
    def _from_db_row(cls, row_dict: dict, database_instance: 'Database') -> 'Website':
        """
        Factory class method to create a Website instance from a database row (dictionary).
        Parses ISO 8601 string timestamps from the database into datetime objects.

        Args:
            row_dict (dict): A dictionary representing a single row from the 'websites' table.
            database_instance (Database): The database instance to associate with the new Website instance.

        Returns:
            Website: An instance of the Website model.
        """
        return cls(
            database=database_instance,
            id_val=row_dict.get('id'),
            website_id=row_dict.get('website_id'),
            property_db_id=row_dict.get('property_db_id'),
            website_url=row_dict.get('website_url'),
            create_time=row_dict.get('create_time'),  # __init__ will parse if string
            update_time=row_dict.get('update_time')   # __init__ will parse if string
        )

    def get_property(self) -> Optional['Property']:
        """
        Retrieves the parent Property instance to which this Website belongs.

        Returns:
            Optional[Property]: The parent Property instance, or None if not found
                                (e.g., if `property_db_id` is invalid or refers to a
                                non-existent property).
        """
        from .property import Property  # Local import to avoid circular dependency
        if self.property_db_id is None:
            logger.warning(f"Website (GA4 ID: {self.website_id}) has no parent 'property_db_id' set. Cannot fetch property.")
            return None
        logger.debug(f"Fetching parent Property for Website (GA4 ID: {self.website_id}) using property_db_id: {self.property_db_id}")
        return Property.find_by_id(self.database, self.property_db_id)

    @classmethod
    def find_by_property_db_id(cls, database_instance: 'Database', property_db_id: int) -> List['Website']:
        """
        Finds all Website instances associated with a given internal Property database ID.

        Args:
            database_instance (Database): The database instance for the query.
            property_db_id (int): The internal database ID of the parent Property.

        Returns:
            List[Website]: A list of Website instances linked to the specified property DB ID.
                           Returns an empty list if no websites are found or an error occurs.
        """
        if property_db_id is None:
            logger.warning("Attempted to find websites by property_db_id with a None ID.")
            return []
        logger.debug(f"Finding websites by parent property_db_id: {property_db_id}")
        return cls.find_all(database_instance, filters={'property_db_id': property_db_id}, order_by="website_url ASC")

    @classmethod
    def find_by_ga4_website_id(cls, database_instance: 'Database', ga4_website_id: str) -> Optional['Website']:
        """
        Finds a single Website instance by its unique GA4 Data Stream ID.

        Args:
            database_instance (Database): The database instance for the query.
            ga4_website_id (str): The GA4 Data Stream ID (e.g., 'properties/123/dataStreams/456').

        Returns:
            Optional[Website]: The Website instance if found, otherwise None.
        """
        if not ga4_website_id:
            logger.warning("Attempted to find website by GA4 website ID with an empty or None ID.")
            return None
        logger.debug(f"Finding website by GA4 Website ID (Data Stream ID): '{ga4_website_id}'")
        # 'website_id' is the column name in the 'websites' table for the GA4 Data Stream ID
        results = cls.find_all(database_instance, filters={'website_id': ga4_website_id}, limit=1)
        return results[0] if results else None


    def __repr__(self) -> str:
        """
        Provides a developer-friendly string representation of the Website instance.
        """
        return (
            f"<Website(id={self.id}, website_id='{self.website_id}', "
            f"url='{self.website_url}', property_db_id={self.property_db_id})>"
        )