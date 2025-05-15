import logging
import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Union

from flask import current_app

from app.models.report import Report
from app.models.report_data import ReportData
from app.services import get_service

# Check if ReportLab is available for PDF generation
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logging.warning("ReportLab not available. PDF report generation will be disabled.")

logger = logging.getLogger(__name__)

class ReportService:
    """
    Service for generating and managing analytics reports.
    
    This service provides methods to:
    - Create new reports
    - Process report data using plugins
    - Generate PDF and HTML reports
    - Store and retrieve report data
    """
    
    def __init__(self):
        """Initialize the Report Service."""
        self.reports_dir = current_app.config.get('REPORTS_DIR', 'reports')
        
        # Ensure reports directory exists
        os.makedirs(self.reports_dir, exist_ok=True)
        
        # Create subdirectories for different report formats
        os.makedirs(os.path.join(self.reports_dir, 'pdf'), exist_ok=True)
        os.makedirs(os.path.join(self.reports_dir, 'html'), exist_ok=True)
        os.makedirs(os.path.join(self.reports_dir, 'json'), exist_ok=True)
        
        logger.info("Report Service initialized")
    
    def create_report(self, report_name: str, report_type: str, parameters: Dict[str, Any]) -> int:
        """
        Create a new report record.
        
        Args:
            report_name: Name of the report
            report_type: Type of report (e.g., 'traffic', 'engagement')
            parameters: Dictionary of parameters for generating the report
            
        Returns:
            ID of the created report
        """
        # Create a new Report instance
        report = Report(
            report_name=report_name,
            report_type=report_type,
            parameters=json.dumps(parameters),
            status='pending'
        )
        
        # Save the report to get an ID
        report_id = report.save()
        
        logger.info(f"Created new report: {report_name} (ID: {report_id})")
        return report_id
    
    def generate_report(self, report_id: int, format_type: str = 'pdf') -> Optional[str]:
        """
        Generate a report based on stored parameters.
        
        Args:
            report_id: ID of the report to generate
            format_type: Format of the report ('pdf', 'html', or 'json')
            
        Returns:
            Path to the generated report file, or None if generation failed
        """
        # Update report status
        report = Report.find_by_id(report_id)
        if not report:
            logger.error(f"Report with ID {report_id} not found")
            return None
        
        report.status = 'generating'
        report.save()
        
        try:
            # Parse parameters
            parameters = json.loads(report.parameters) if report.parameters else {}
            
            # Use plugin service to get the right plugin for the report type
            plugin_service = get_service('plugin')
            if not plugin_service:
                logger.error("Plugin service not available")
                self._update_report_status(report_id, 'failed', "Plugin service not available")
                return None
            
            # Determine which plugin to use based on report type
            plugin_id = parameters.get('plugin_id')
            if not plugin_id:
                if report.report_type == 'traffic':
                    plugin_id = 'traffic_metrics'
                elif report.report_type == 'engagement':
                    plugin_id = 'engagement_metrics'
                else:
                    plugin_id = report.report_type  # Use report type as plugin ID
            
            # Process data using the appropriate plugin
            ga4_service = get_service('ga4')
            if not ga4_service or not ga4_service.is_available():
                logger.error("GA4 service not available")
                self._update_report_status(report_id, 'failed', "GA4 service not available")
                return None
            
            # Get the plugin instance
            plugin = plugin_service.get_plugin_instance(plugin_id)
            if not plugin:
                logger.error(f"Plugin '{plugin_id}' not found")
                self._update_report_status(report_id, 'failed', f"Plugin '{plugin_id}' not found")
                return None
            
            # Process data using the plugin
            data = plugin.process_data(parameters)
            
            # Store the processed data
            self._store_report_data(report_id, data)
            
            # Generate the report file in the requested format
            if format_type == 'pdf':
                if not REPORTLAB_AVAILABLE:
                    logger.warning("PDF generation requested but ReportLab not available")
                    report_path = self._generate_json_report(report_id, data)
                else:
                    report_path = self._generate_pdf_report(report_id, data)
            elif format_type == 'html':
                report_path = self._generate_html_report(report_id, data)
            else:  # Default to JSON
                report_path = self._generate_json_report(report_id, data)
            
            # Update report status and file path
            if report_path:
                self._update_report_status(report_id, 'completed', file_path=report_path)
                logger.info(f"Successfully generated report {report_id} at {report_path}")
                return report_path
            else:
                self._update_report_status(report_id, 'failed', "Report generation failed")
                return None
                
        except Exception as e:
            logger.error(f"Error generating report {report_id}: {str(e)}", exc_info=True)
            self._update_report_status(report_id, 'failed', str(e))
            return None
    
    def get_report_status(self, report_id: int) -> Dict[str, Any]:
        """
        Get the status of a report.
        
        Args:
            report_id: ID of the report
            
        Returns:
            Dictionary containing report status information
        """
        report = Report.find_by_id(report_id)
        if not report:
            return {'status': 'not_found', 'message': f"Report ID {report_id} not found"}
        
        result = {
            'id': report.id,
            'name': report.report_name,
            'type': report.report_type,
            'status': report.status,
            'created_at': report.created_at.isoformat() if report.created_at else None,
            'file_path': report.file_path
        }
        
        return result
    
    def get_report_data(self, report_id: int) -> List[Dict[str, Any]]:
        """
        Get the stored data for a report.
        
        Args:
            report_id: ID of the report
            
        Returns:
            List of dictionaries containing report data
        """
        report_data = ReportData.find_by_report_id(report_id)
        return [data.to_dict() for data in report_data]
    
    def delete_report(self, report_id: int) -> bool:
        """
        Delete a report and its associated data and files.
        
        Args:
            report_id: ID of the report to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        report = Report.find_by_id(report_id)
        if not report:
            logger.warning(f"Report with ID {report_id} not found for deletion")
            return False
        
        # Delete associated report data
        ReportData.delete_by_report_id(report_id)
        
        # Delete report file if it exists
        if report.file_path and os.path.exists(report.file_path):
            try:
                os.remove(report.file_path)
                logger.info(f"Deleted report file: {report.file_path}")
            except Exception as e:
                logger.error(f"Error deleting report file {report.file_path}: {str(e)}")
        
        # Delete the report record
        report.delete()
        logger.info(f"Deleted report with ID {report_id}")
        
        return True
    
    def list_reports(self, limit: int = 50, offset: int = 0, 
                     report_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List available reports with optional filtering.
        
        Args:
            limit: Maximum number of reports to return
            offset: Offset for pagination
            report_type: Optional filter by report type
            
        Returns:
            List of report dictionaries
        """
        if report_type:
            reports = Report.find_by_type(report_type, limit, offset)
        else:
            reports = Report.find_all(limit, offset)
        
        return [report.to_dict() for report in reports]
    
    def _update_report_status(self, report_id: int, status: str, 
                             message: Optional[str] = None, 
                             file_path: Optional[str] = None) -> None:
        """
        Update the status of a report.
        
        Args:
            report_id: ID of the report
            status: New status ('pending', 'generating', 'completed', 'failed')
            message: Optional status message or error information
            file_path: Optional path to the generated report file
        """
        report = Report.find_by_id(report_id)
        if not report:
            logger.error(f"Report with ID {report_id} not found for status update")
            return
        
        report.status = status
        if file_path:
            report.file_path = file_path
        
        # Store message in parameters if provided
        if message:
            try:
                params = json.loads(report.parameters) if report.parameters else {}
                params['status_message'] = message
                report.parameters = json.dumps(params)
            except json.JSONDecodeError:
                # If parameters is not valid JSON, create a new one
                report.parameters = json.dumps({'status_message': message})
        
        report.save()
        logger.debug(f"Updated report {report_id} status to '{status}'")
    
    def _store_report_data(self, report_id: int, data: Dict[str, Any]) -> None:
        """
        Store processed report data in the database.
        
        Args:
            report_id: ID of the report
            data: The processed data to store
        """
        # Delete any existing data for this report
        ReportData.delete_by_report_id(report_id)
        
        # Extract metrics and dimensions from the raw data
        raw_data = data.get('raw_data', [])
        current_time = datetime.utcnow()
        
        for item in raw_data:
            # Check if we have a property ID in the data
            property_id = data.get('metadata', {}).get('property_id', '')
            
            # Extract date if available
            data_date = item.get('date', '')
            
            # Store each metric-dimension pair
            for key, value in item.items():
                if key == 'date':
                    continue  # Skip date field as we already extracted it
                
                # Determine if this is a metric or dimension
                # In GA4, dimensions are typically string values and metrics are numeric
                try:
                    float(value)  # Try to convert to float to see if it's a metric
                    is_metric = True
                except (ValueError, TypeError):
                    is_metric = False
                
                if is_metric:
                    # Store as a metric
                    report_data = ReportData(
                        report_db_id=report_id,
                        property_ga4_id=property_id,
                        metric_name=key,
                        metric_value=value,
                        data_date=data_date
                    )
                else:
                    # Store as a dimension
                    report_data = ReportData(
                        report_db_id=report_id,
                        property_ga4_id=property_id,
                        dimension_name=key,
                        dimension_value=value,
                        data_date=data_date
                    )
                
                report_data.save()
        
        logger.info(f"Stored {len(raw_data)} data points for report {report_id}")
    
    def _generate_pdf_report(self, report_id: int, data: Dict[str, Any]) -> Optional[str]:
        """
        Generate a PDF report from the processed data.
        
        Args:
            report_id: ID of the report
            data: The processed data to include in the report
            
        Returns:
            Path to the generated PDF file, or None if generation failed
        """
        if not REPORTLAB_AVAILABLE:
            logger.error("Cannot generate PDF: ReportLab library not available")
            return None
        
        try:
            # Get report metadata
            report = Report.find_by_id(report_id)
            if not report:
                logger.error(f"Report with ID {report_id} not found")
                return None
            
            # Generate a unique filename
            filename = f"{report.report_type}_{report_id}_{uuid.uuid4().hex[:8]}.pdf"
            filepath = os.path.join(self.reports_dir, 'pdf', filename)
            
            # Create the PDF document
            doc = SimpleDocTemplate(filepath, pagesize=letter)
            styles = getSampleStyleSheet()
            elements = []
            
            # Add title
            title_style = styles["Heading1"]
            elements.append(Paragraph(report.report_name, title_style))
            elements.append(Spacer(1, 12))
            
            # Add metadata
            metadata = data.get('metadata', {})
            elements.append(Paragraph(f"Report Type: {report.report_type}", styles["Normal"]))
            elements.append(Paragraph(f"Property ID: {metadata.get('property_id', 'N/A')}", styles["Normal"]))
            elements.append(Paragraph(f"Date Range: {metadata.get('date_range', 'N/A')}", styles["Normal"]))
            elements.append(Paragraph(f"Generated: {metadata.get('generated_at', datetime.now().isoformat())}", styles["Normal"]))
            elements.append(Spacer(1, 12))
            
            # Add summary section if available
            summary = data.get('summary', {})
            if summary:
                elements.append(Paragraph("Summary", styles["Heading2"]))
                elements.append(Spacer(1, 6))
                
                # Create a table for summary data
                summary_data = [["Metric", "Value"]]
                for key, value in summary.items():
                    formatted_key = key.replace('_', ' ').replace('avg', 'Average').title()
                    formatted_value = f"{value:.2f}" if isinstance(value, float) else str(value)
                    summary_data.append([formatted_key, formatted_value])
                
                summary_table = Table(summary_data, colWidths=[300, 150])
                summary_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                elements.append(summary_table)
                elements.append(Spacer(1, 12))
            
            # Add trends section if available
            trends = data.get('trends', {})
            if trends:
                elements.append(Paragraph("Trends", styles["Heading2"]))
                elements.append(Spacer(1, 6))
                
                # Create a table for trend data
                trend_data = [["Metric", "Change", "% Change", "Direction"]]
                for key, trend in trends.items():
                    formatted_key = key.replace('_', ' ').title()
                    formatted_change = f"{trend.get('change', 0):.2f}"
                    formatted_percent = f"{trend.get('percent_change', 0):.2f}%"
                    direction = trend.get('direction', 'neutral')
                    trend_data.append([formatted_key, formatted_change, formatted_percent, direction])
                
                trend_table = Table(trend_data, colWidths=[150, 100, 100, 100])
                trend_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                elements.append(trend_table)
                elements.append(Spacer(1, 12))
            
            # Add raw data table if available
            raw_data = data.get('raw_data', [])
            if raw_data and len(raw_data) > 0:
                elements.append(Paragraph("Data Points", styles["Heading2"]))
                elements.append(Spacer(1, 6))
                
                # Get column headers from the first data point
                headers = list(raw_data[0].keys())
                
                # Create a table for raw data
                table_data = [headers]
                for item in raw_data:
                    row = [str(item.get(h, '')) for h in headers]
                    table_data.append(row)
                
                # Calculate column widths based on header length
                col_widths = [max(80, len(h) * 12) for h in headers]
                col_widths = [min(w, 200) for w in col_widths]  # Limit max width
                
                data_table = Table(table_data, colWidths=col_widths)
                data_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                elements.append(data_table)
            
            # Build the PDF
            doc.build(elements)
            logger.info(f"Generated PDF report at {filepath}")
            
            return filepath
        
        except Exception as e:
            logger.error(f"Error generating PDF report: {str(e)}", exc_info=True)
            return None
    
    def _generate_html_report(self, report_id: int, data: Dict[str, Any]) -> Optional[str]:
        """
        Generate an HTML report from the processed data.
        
        Args:
            report_id: ID of the report
            data: The processed data to include in the report
            
        Returns:
            Path to the generated HTML file, or None if generation failed
        """
        try:
            # Get report metadata
            report = Report.find_by_id(report_id)
            if not report:
                logger.error(f"Report with ID {report_id} not found")
                return None
            
            # Generate a unique filename
            filename = f"{report.report_type}_{report_id}_{uuid.uuid4().hex[:8]}.html"
            filepath = os.path.join(self.reports_dir, 'html', filename)
            
            # Get metadata
            metadata = data.get('metadata', {})
            summary = data.get('summary', {})
            trends = data.get('trends', {})
            raw_data = data.get('raw_data', [])
            
            # Build HTML content
            html_content = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{report.report_name}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    h1, h2, h3 {{ color: #333; }}
                    table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                    tr:nth-child(even) {{ background-color: #f9f9f9; }}
                    .metadata {{ background-color: #f5f5f5; padding: 10px; border-radius: 5px; margin-bottom: 20px; }}
                    .trend-up {{ color: green; }}
                    .trend-down {{ color: red; }}
                    .trend-flat {{ color: gray; }}
                </style>
            </head>
            <body>
                <h1>{report.report_name}</h1>
                
                <div class="metadata">
                    <p><strong>Report Type:</strong> {report.report_type}</p>
                    <p><strong>Property ID:</strong> {metadata.get('property_id', 'N/A')}</p>
                    <p><strong>Date Range:</strong> {metadata.get('date_range', 'N/A')}</p>
                    <p><strong>Generated:</strong> {metadata.get('generated_at', datetime.now().isoformat())}</p>
                </div>
            """
            
            # Add summary section
            if summary:
                html_content += """
                <h2>Summary</h2>
                <table>
                    <tr>
                        <th>Metric</th>
                        <th>Value</th>
                    </tr>
                """
                
                for key, value in summary.items():
                    formatted_key = key.replace('_', ' ').replace('avg', 'Average').title()
                    formatted_value = f"{value:.2f}" if isinstance(value, float) else str(value)
                    html_content += f"""
                    <tr>
                        <td>{formatted_key}</td>
                        <td>{formatted_value}</td>
                    </tr>
                    """
                
                html_content += "</table>"
            
            # Add trends section
            if trends:
                html_content += """
                <h2>Trends</h2>
                <table>
                    <tr>
                        <th>Metric</th>
                        <th>Change</th>
                        <th>% Change</th>
                        <th>Direction</th>
                    </tr>
                """
                
                for key, trend in trends.items():
                    formatted_key = key.replace('_', ' ').title()
                    formatted_change = f"{trend.get('change', 0):.2f}"
                    formatted_percent = f"{trend.get('percent_change', 0):.2f}%"
                    direction = trend.get('direction', 'neutral')
                    
                    trend_class = ""
                    if direction == 'up':
                        trend_class = "trend-up"
                    elif direction == 'down':
                        trend_class = "trend-down"
                    else:
                        trend_class = "trend-flat"
                    
                    html_content += f"""
                    <tr>
                        <td>{formatted_key}</td>
                        <td>{formatted_change}</td>
                        <td>{formatted_percent}</td>
                        <td class="{trend_class}">{direction.title()}</td>
                    </tr>
                    """
                
                html_content += "</table>"
            
            # Add raw data section
            if raw_data and len(raw_data) > 0:
                html_content += "<h2>Data Points</h2>"
                
                # Get column headers
                headers = list(raw_data[0].keys())
                
                html_content += "<table><tr>"
                for header in headers:
                    formatted_header = header.replace('_', ' ').title()
                    html_content += f"<th>{formatted_header}</th>"
                html_content += "</tr>"
                
                # Add data rows
                for item in raw_data:
                    html_content += "<tr>"
                    for header in headers:
                        value = item.get(header, '')
                        html_content += f"<td>{value}</td>"
                    html_content += "</tr>"
                
                html_content += "</table>"
            
            # Close HTML content
            html_content += """
            </body>
            </html>
            """
            
            # Write HTML file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"Generated HTML report at {filepath}")
            return filepath
        
        except Exception as e:
            logger.error(f"Error generating HTML report: {str(e)}", exc_info=True)
            return None
    
    def _generate_json_report(self, report_id: int, data: Dict[str, Any]) -> Optional[str]:
        """
        Generate a JSON report from the processed data.
        
        Args:
            report_id: ID of the report
            data: The processed data to include in the report
            
        Returns:
            Path to the generated JSON file, or None if generation failed
        """
        try:
            # Get report metadata
            report = Report.find_by_id(report_id)
            if not report:
                logger.error(f"Report with ID {report_id} not found")
                return None
            
            # Generate a unique filename
            filename = f"{report.report_type}_{report_id}_{uuid.uuid4().hex[:8]}.json"
            filepath = os.path.join(self.reports_dir, 'json', filename)
            
            # Prepare report data with additional metadata
            report_data = {
                'report_id': report_id,
                'report_name': report.report_name,
                'report_type': report.report_type,
                'generated_at': datetime.utcnow().isoformat(),
                'data': data
            }
            
            # Write JSON file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2)
            
            logger.info(f"Generated JSON report at {filepath}")
            return filepath
        
        except Exception as e:
            logger.error(f"Error generating JSON report: {str(e)}", exc_info=True)
            return None