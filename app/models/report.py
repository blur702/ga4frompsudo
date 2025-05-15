"""
Report Model.
Represents metadata for generated analytics reports.
"""

import logging
import datetime
import json  # For serializing/deserializing parameters
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from .base_model import BaseModel

if TYPE_CHECKING:
    from .database import Database

logger = logging.getLogger(__name__)

class Report(BaseModel):
    """
    Represents metadata for a generated or to-be-generated analytics report.

    This class stores information about a report, such as its name, type
    (which might determine the generation logic or plugin used), the parameters
    it was generated with, its creation timestamp, current status (e.g., pending,
    completed, failed), and a path to the actual report file if one is produced.
    
    Attributes:
        id (int): The primary key ID in the database
        report_name (str): The user-defined or system-generated name for the report.
        report_type (str): A string identifying the type of report (e.g., 'traffic',
                           'engagement', 'custom_plugin_report').
        parameters (str): A JSON string of parameters used to generate the report.
        created_at (datetime.datetime): Timestamp when this report record was created.
        status (str): The current status of the report generation process
                     (e.g., 'pending', 'generating', 'completed', 'failed').
        file_path (str): The filesystem path to the generated report file (e.g., a PDF).
    """
    table_name = 'reports'

    def __init__(self, 
                 id: Optional[int] = None,
                 report_name: str = "",
                 report_type: str = "",
                 parameters: str = "",
                 created_at: Optional[datetime.datetime] = None,
                 status: str = 'pending',
                 file_path: Optional[str] = None):
        """
        Initializes a new instance of the Report model.

        Args:
            id: The primary key ID in the database
            report_name: The name of the report
            report_type: The type of the report
            parameters: JSON string of parameters used for report generation
            created_at: Report record creation timestamp
            status: Current status of the report. Defaults to 'pending'
            file_path: Path to the generated report file
        """
        super().__init__(id, created_at)
        self.report_name = report_name
        self.report_type = report_type
        self.parameters = parameters
        self.status = status
        self.file_path = file_path

    def to_dict(self, exclude_params: bool = False) -> dict:
        """
        Converts the Report instance to a dictionary.
        
        Args:
            exclude_params: Whether to exclude the parameters field
            
        Returns:
            Dictionary representation of the report
        """
        data = {
            'id': self.id,
            'report_name': self.report_name,
            'report_type': self.report_type,
            'status': self.status,
            'created_at': self._format_datetime(self.created_at),
            'file_path': self.file_path
        }
        
        if not exclude_params:
            data['parameters'] = self.parameters
            
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Report':
        """
        Creates a Report instance from a dictionary.
        
        Args:
            data: Dictionary containing report data
            
        Returns:
            Report instance
        """
        return cls(
            id=data.get('id'),
            report_name=data.get('report_name', ''),
            report_type=data.get('report_type', ''),
            parameters=data.get('parameters', ''),
            created_at=cls._parse_datetime(data.get('created_at')),
            status=data.get('status', 'pending'),
            file_path=data.get('file_path')
        )

    def get_data(self) -> List['ReportData']:
        """
        Retrieves all ReportData instances associated with this Report's database ID.

        Returns:
            List of ReportData model instances linked to this report
        """
        from .report_data import ReportData  # Local import to avoid circular dependency
        if self.id is None:
            logger.warning(
                f"Report '{self.report_name}' has no ID. Cannot fetch report data. Save the report first."
            )
            return []
        
        logger.debug(f"Fetching data for Report (ID: {self.id}, Name: '{self.report_name}')")
        return ReportData.find_by_report_id(self.id)

    def update_status(self, new_status: str, file_path: Optional[str] = None) -> bool:
        """
        Updates the status of the report and optionally its file path, then saves the changes.

        Args:
            new_status: The new status for the report
            file_path: The new file path if the report generation is completed
            
        Returns:
            True if the status was successfully updated and saved, False otherwise
        """
        if not self.id:
            logger.error(f"Cannot update status for report '{self.report_name}' as it has no ID (not saved).")
            return False

        logger.info(f"Updating status for report ID {self.id} ('{self.report_name}') to '{new_status}'.")
        self.status = new_status
        if file_path is not None:
            self.file_path = file_path
        elif new_status == 'completed' and self.file_path is None:
            logger.warning(f"Report ID {self.id} status updated to 'completed' but no file_path provided and current is None.")

        return self.save() > 0  # save() returns ID > 0 if successful

    @classmethod
    def find_by_type(cls, report_type: str, limit: int = 50, offset: int = 0) -> List['Report']:
        """
        Finds all Report instances of a specific type, ordered by creation time (most recent first).

        Args:
            report_type: The type of reports to find
            limit: Maximum number of reports to return
            offset: Number of reports to skip
            
        Returns:
            List of Report instances of the specified type
        """
        logger.debug(f"Finding reports by type: '{report_type}'")
        query = f"SELECT * FROM {cls.table_name} WHERE report_type = ? ORDER BY created_at DESC LIMIT ? OFFSET ?"
        results = cls.execute_query(query, (report_type, limit, offset))
        return [cls.from_dict(row) for row in results]

    @classmethod
    def find_by_status(cls, status: str, limit: int = 50, offset: int = 0) -> List['Report']:
        """
        Finds all Report instances with a specific status, ordered by creation time (most recent first).

        Args:
            status: The status to filter reports by
            limit: Maximum number of reports to return
            offset: Number of reports to skip
            
        Returns:
            List of Report instances with the specified status
        """
        logger.debug(f"Finding reports by status: '{status}'")
        query = f"SELECT * FROM {cls.table_name} WHERE status = ? ORDER BY created_at DESC LIMIT ? OFFSET ?"
        results = cls.execute_query(query, (status, limit, offset))
        return [cls.from_dict(row) for row in results]

    def __repr__(self) -> str:
        """
        Provides a developer-friendly string representation of the Report instance.
        """
        created_str = self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else 'N/A'
        return (
            f"<Report(id={self.id}, name='{self.report_name}', type='{self.report_type}', "
            f"status='{self.status}', created='{created_str}')>"
        )