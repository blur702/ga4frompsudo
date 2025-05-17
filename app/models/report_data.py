"""
Report Data Model.
Stores individual data points or metrics associated with a generated Report.
"""

import logging
import datetime
from typing import Optional, List, Any, Dict, TYPE_CHECKING
from .base_model import BaseModel

if TYPE_CHECKING:
    from .report import Report       # pylint: disable=cyclic-import
    from .property import Property   # pylint: disable=cyclic-import
    from .database import Database

logger = logging.getLogger(__name__)

class ReportData(BaseModel):
    """
    Represents an individual piece of data or a metric belonging to a generated Report.
    
    This model is designed to be flexible, storing various types of data points that
    might make up a report, such as specific metrics, their values, associated dimensions,
    the relevant date, and a link back to the parent Report.
    
    Attributes:
        id (int): The primary key ID in the database
        report_db_id (int): The ID of the Report this data belongs to (foreign key)
        property_ga4_id (str): The GA4 Property ID this data point relates to
        metric_name (str): The name of the metric (e.g., 'totalUsers', 'sessions')
        metric_value (str): The value of the metric, stored as string
        dimension_name (str): The name of the dimension (e.g., 'date', 'country')
        dimension_value (str): The value of the dimension
        data_date (str): The date this data point refers to in YYYY-MM-DD format
        timestamp (datetime): When this data point was recorded
    """
    table_name = 'report_data'
    
    def __init__(self,
                 id: Optional[int] = None,
                 report_db_id: Optional[int] = None,
                 property_ga4_id: Optional[str] = None,
                 metric_name: Optional[str] = None,
                 metric_value: Optional[str] = None,
                 dimension_name: Optional[str] = None,
                 dimension_value: Optional[str] = None,
                 data_date: Optional[str] = None,
                 timestamp: Optional[datetime.datetime] = None,
                 created_at: Optional[datetime.datetime] = None,
                 updated_at: Optional[datetime.datetime] = None):
        """
        Initialize a new ReportData instance.
        
        Args:
            id: The primary key ID in the database
            report_db_id: The ID of the Report this data belongs to
            property_ga4_id: The GA4 Property ID this data relates to
            metric_name: The name of the metric
            metric_value: The value of the metric
            dimension_name: The name of the dimension
            dimension_value: The value of the dimension
            data_date: The date this data refers to
            timestamp: When this data point was recorded
            created_at: When this record was created
            updated_at: When this record was last updated
        """
        super().__init__(id, created_at, updated_at)
        self.report_db_id = report_db_id
        self.property_ga4_id = property_ga4_id
        self.metric_name = metric_name
        self.metric_value = metric_value
        self.dimension_name = dimension_name
        self.dimension_value = dimension_value
        self.data_date = data_date
        self.timestamp = timestamp if timestamp else datetime.datetime.now(datetime.timezone.utc)

    def to_dict(self) -> dict:
        """
        Converts the ReportData instance to a dictionary.
        
        Returns:
            Dictionary representation of the report data
        """
        return {
            'id': self.id,
            'report_db_id': self.report_db_id,
            'property_ga4_id': self.property_ga4_id,
            'metric_name': self.metric_name,
            'metric_value': self.metric_value,
            'dimension_name': self.dimension_name,
            'dimension_value': self.dimension_value,
            'data_date': self.data_date,
            'timestamp': self._format_datetime(self.timestamp),
            'created_at': self._format_datetime(self.created_at),
            'updated_at': self._format_datetime(self.updated_at)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReportData':
        """
        Creates a ReportData instance from a dictionary.
        
        Args:
            data: Dictionary containing report data
            
        Returns:
            ReportData instance
        """
        return cls(
            id=data.get('id'),
            report_db_id=data.get('report_db_id'),
            property_ga4_id=data.get('property_ga4_id'),
            metric_name=data.get('metric_name'),
            metric_value=data.get('metric_value'),
            dimension_name=data.get('dimension_name'),
            dimension_value=data.get('dimension_value'),
            data_date=data.get('data_date'),
            timestamp=cls._parse_datetime(data.get('timestamp')),
            created_at=cls._parse_datetime(data.get('created_at')),
            updated_at=cls._parse_datetime(data.get('updated_at'))
        )

    def get_report(self) -> Optional['Report']:
        """
        Retrieves the parent Report instance to which this ReportData record belongs.

        Returns:
            The parent Report instance, or None if not found
        """
        from .report import Report  # Local import
        if self.report_db_id is None:
            logger.warning("ReportData instance has no report_db_id. Cannot fetch report.")
            return None
        logger.debug(f"Fetching parent Report for ReportData ID {self.id}")
        return Report.find_by_id(self.report_db_id)

    def get_property(self) -> Optional['Property']:
        """
        Retrieves the GA4 Property instance this ReportData record is associated with.

        Returns:
            The associated Property instance, or None if not found
        """
        from .property import Property  # Local import
        if not self.property_ga4_id:
            logger.debug(f"ReportData ID {self.id} has no property_ga4_id. Cannot fetch property.")
            return None
        logger.debug(f"Fetching Property for ReportData ID {self.id}")
        return Property.find_by_property_id(self.property_ga4_id)

    @classmethod
    def find_by_report_id(cls, report_id: int) -> List['ReportData']:
        """
        Finds all ReportData instances associated with a given Report ID.
        
        Args:
            report_id: The ID of the parent Report
            
        Returns:
            List of ReportData instances linked to the report
        """
        if report_id is None:
            logger.warning("Attempted to find report data with a None report_id.")
            return []
        logger.debug(f"Finding all report data for report_id: {report_id}")
        query = f"SELECT * FROM {cls.table_name} WHERE report_db_id = ? ORDER BY timestamp ASC, id ASC"
        results = cls.execute_query(query, (report_id,))
        return [cls.from_dict(row) for row in results]

    @classmethod
    def delete_by_report_id(cls, report_id: int) -> int:
        """
        Deletes all ReportData instances associated with a given Report ID.
        
        Args:
            report_id: The ID of the parent Report
            
        Returns:
            Number of records deleted
        """
        if report_id is None:
            logger.warning("Attempted to delete report data with a None report_id.")
            return 0
        logger.debug(f"Deleting all report data for report_id: {report_id}")
        query = f"DELETE FROM {cls.table_name} WHERE report_db_id = ?"
        return cls.execute_update(query, (report_id,))

    @classmethod
    def find_by_property_and_date(cls, property_id: str, data_date: str) -> List['ReportData']:
        """
        Finds all ReportData instances for a specific GA4 property ID and date.
        
        Args:
            property_id: The GA4 Property ID to filter by
            data_date: The date to filter by (YYYY-MM-DD)
            
        Returns:
            List of ReportData instances
        """
        if not property_id or not data_date:
            logger.warning("Missing required parameters for find_by_property_and_date.")
            return []
        
        logger.debug(f"Finding report data for property_id: '{property_id}' and date: '{data_date}'")
        query = f"SELECT * FROM {cls.table_name} WHERE property_ga4_id = ? AND data_date = ? ORDER BY metric_name ASC"
        results = cls.execute_query(query, (property_id, data_date))
        return [cls.from_dict(row) for row in results]

    def __repr__(self) -> str:
        """
        Provides a developer-friendly string representation of the ReportData instance.
        """
        return (
            f"<ReportData(id={self.id}, report_db_id={self.report_db_id}, "
            f"metric='{self.metric_name}'='{self.metric_value}', date='{self.data_date}')>"
        )