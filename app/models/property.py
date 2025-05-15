"""
GA4 Property Model.
Represents a Google Analytics 4 property, including its attributes and
relationships with other models like Websites and Reports.
"""

import logging
import datetime
from .base_model import BaseModel

logger = logging.getLogger(__name__)

class Property(BaseModel):
    """
    Represents a Google Analytics 4 (GA4) property.

    This class stores details about a GA4 property, such as its ID, name,
    associated account ID, and timestamps. It inherits common database
    operations from BaseModel.

    Attributes:
        property_id (str): The unique identifier for the GA4 property (e.g., 'properties/123456789').
        property_name (str, optional): The display name of the GA4 property.
        account_id (str, optional): The identifier of the GA4 account this property belongs to.
        create_time (datetime.datetime, optional): The timestamp when the property was created in GA4.
        update_time (datetime.datetime, optional): The timestamp when the property was last updated in GA4.
        # `id` and `database` attributes are inherited from BaseModel.
    """

    @property
    def TABLE_NAME(self) -> str:
        """Returns the database table name for Property records."""
        return 'properties'

    def __init__(self, database,
                 property_id: str,
                 property_name: str = None,
                 account_id: str = None,
                 create_time = None,  # Can be str or datetime
                 update_time = None,  # Can be str or datetime
                 id_val: int = None):
        """
        Initializes a new instance of the Property model.

        Args:
            database (Database): The database instance for operations.
            property_id (str): The unique GA4 property ID. This is mandatory.
            property_name (str, optional): The display name of the property.
            account_id (str, optional): The GA4 account ID associated with this property.
            create_time (str or datetime.datetime, optional): Property creation timestamp.
                                                           If str, should be ISO 8601 format.
            update_time (str or datetime.datetime, optional): Property last update timestamp.
                                                           If str, should be ISO 8601 format.
            id_val (int, optional): The internal database ID if the record already exists.

        Raises:
            ValueError: If `property_id` is None or empty.
        """
        super().__init__(database, id_val)
        if not property_id:
            raise ValueError("GA4 Property ID (property_id) is mandatory.")

        self.property_id = property_id
        self.property_name = property_name
        self.account_id = account_id

        # Handle datetime conversion if strings are passed
        self.create_time = self._iso_to_datetime(create_time) if isinstance(create_time, str) else create_time
        self.update_time = self._iso_to_datetime(update_time) if isinstance(update_time, str) else update_time


    def _to_dict(self) -> dict:
        """
        Converts the Property model's attributes to a dictionary for database storage.
        Timestamps are converted to ISO 8601 string format.

        Returns:
            dict: A dictionary representation of the Property instance's fields
                  suitable for database insertion or update.
        """
        return {
            'property_id': self.property_id,
            'property_name': self.property_name,
            'account_id': self.account_id,
            'create_time': self._datetime_to_iso(self.create_time),
            'update_time': self._datetime_to_iso(self.update_time)
        }

    @classmethod
    def _from_db_row(cls, row_dict: dict, database_instance):
        """
        Creates a Property instance from a database row (dictionary).
        Timestamps from the database (ISO 8601 strings) are parsed into datetime objects.

        Args:
            row_dict (dict): A dictionary representing a row from the 'properties' table.
            database_instance (Database): The database instance to associate with the new Property instance.

        Returns:
            Property: An instance of the Property model.
        """
        return cls(
            database=database_instance,
            id_val=row_dict.get('id'),
            property_id=row_dict.get('property_id'),
            property_name=row_dict.get('property_name'),
            account_id=row_dict.get('account_id'),
            create_time=row_dict.get('create_time'),  # Will be parsed by __init__ if str
            update_time=row_dict.get('update_time')   # Will be parsed by __init__ if str
        )

    def get_websites(self):
        """
        Retrieves all Website instances associated with this Property.

        Returns:
            list: A list of Website model instances linked to this property's internal DB ID.
                  Returns an empty list if no websites are found or an error occurs.
        """
        from .website import Website  # Local import to avoid circular dependency issues at module load
        if self.id is None:
            logger.warning(f"Property '{self.property_name}' (GA4 ID: {self.property_id}) has no internal DB ID. Cannot fetch websites.")
            return []
        logger.debug(f"Fetching websites for Property DB ID: {self.id}")
        # Website.find_by_property expects the database ID of the property
        return Website.find_by_property_db_id(self.database, self.id)


    def get_reports(self):
        """
        Retrieves all Report instances associated with this Property.
        Note: This assumes a direct relationship or a way to link reports to properties,
        e.g., if `report_data` links to `property_ga4_id`. A direct link from `reports`
        table to `properties` table might be needed for this to be straightforward.
        For now, this is a placeholder for such functionality.

        Returns:
            list: A list of Report model instances.
        """
        # This is a placeholder - implementation depends on the Report model
        # which hasn't been created yet
        logger.warning(f"get_reports for Property ID {self.property_id} is a placeholder and needs specific linking logic.")
        return []  # Placeholder

    @classmethod
    def find_by_account(cls, database_instance, account_id: str):
        """
        Finds all properties associated with a given GA4 account ID.

        Args:
            database_instance (Database): The database instance.
            account_id (str): The GA4 account ID to filter properties by.

        Returns:
            list: A list of Property instances belonging to the specified account.
                  Returns an empty list if no properties are found or an error occurs.
        """
        logger.debug(f"Finding properties by account ID: {account_id}")
        return cls.find_all(database_instance, filters={'account_id': account_id}, order_by="property_name ASC")

    @classmethod
    def find_by_ga4_property_id(cls, database_instance, ga4_property_id: str):
        """
        Finds a property by its unique GA4 Property ID.

        Args:
            database_instance (Database): The database instance.
            ga4_property_id (str): The GA4 Property ID (e.g., 'properties/12345').

        Returns:
            Property or None: The Property instance if found, otherwise None.
        """
        logger.debug(f"Finding property by GA4 Property ID: {ga4_property_id}")
        # Assuming 'property_id' is the column name for GA4 Property ID in the DB
        results = cls.find_all(database_instance, filters={'property_id': ga4_property_id}, limit=1)
        return results[0] if results else None

    def __repr__(self):
        """
        Provides a developer-friendly string representation of the Property instance.
        """
        return (f"<Property(id={self.id}, property_id='{self.property_id}', "
                f"name='{self.property_name}', account_id='{self.account_id}')>")