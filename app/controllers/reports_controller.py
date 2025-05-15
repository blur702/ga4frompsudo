"""
Reports controller for handling report generation, viewing, and management.
"""

import logging
import json
import os
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, jsonify, current_app

from app.services import get_service
from app.controllers.auth_controller import login_required

logger = logging.getLogger(__name__)

# Create blueprint
reports_bp = Blueprint('reports', __name__, url_prefix='/reports')

@reports_bp.route('/')
@login_required
def index():
    """
    Display a list of all reports.
    """
    # Get report service
    report_service = get_service('report')
    if not report_service:
        flash('Report service is not available.', 'warning')
        return redirect(url_for('dashboard.index'))
    
    try:
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        offset = (page - 1) * limit
        
        # Get filter parameters
        report_type = request.args.get('type')
        
        # Get reports
        reports = report_service.list_reports(limit=limit, offset=offset, report_type=report_type)
        
        # Render reports list
        return render_template('reports/index.html',
                              reports=reports,
                              page=page,
                              limit=limit,
                              report_type=report_type)
    
    except Exception as e:
        logger.error(f"Error loading reports list: {str(e)}", exc_info=True)
        flash('An error occurred while loading the reports list.', 'error')
        return redirect(url_for('dashboard.index'))

@reports_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_report():
    """
    Create a new report.
    
    GET: Display the report creation form
    POST: Process the report creation form submission
    """
    # Get required services
    report_service = get_service('report')
    ga4_service = get_service('ga4')
    plugin_service = get_service('plugin')
    
    if not report_service:
        flash('Report service is not available.', 'warning')
        return redirect(url_for('reports.index'))
    
    if not ga4_service or not ga4_service.is_available():
        flash('Google Analytics service is not available. Check your credentials.', 'warning')
        return redirect(url_for('reports.index'))
    
    if not plugin_service:
        flash('Plugin service is not available.', 'warning')
        return redirect(url_for('reports.index'))
    
    # Handle form submission
    if request.method == 'POST':
        report_name = request.form.get('report_name', '')
        report_type = request.form.get('report_type', '')
        property_id = request.form.get('property_id', '')
        date_range = request.form.get('date_range', 'last30days')
        plugin_id = request.form.get('plugin_id', '')
        
        # Validate inputs
        if not report_name or not report_type or not property_id:
            flash('Report name, type, and property ID are required.', 'error')
            return redirect(url_for('reports.new_report'))
        
        # Check if plugin exists
        if plugin_id and not plugin_service.get_plugin_instance(plugin_id):
            flash(f'Plugin with ID {plugin_id} not found.', 'error')
            return redirect(url_for('reports.new_report'))
        
        try:
            # Create parameters object
            parameters = {
                'property_id': property_id,
                'date_range': date_range,
                'plugin_id': plugin_id or report_type  # Use report_type as plugin_id if not specified
            }
            
            # Create the report
            report_id = report_service.create_report(
                report_name=report_name,
                report_type=report_type,
                parameters=parameters
            )
            
            # Generate the report asynchronously
            # In a production app, this would be handled by a background task
            # For simplicity, we'll generate it synchronously here
            report_path = report_service.generate_report(report_id, format_type='html')
            
            if report_path:
                flash(f'Report "{report_name}" created successfully.', 'success')
            else:
                flash(f'Report "{report_name}" created but generation failed.', 'warning')
            
            return redirect(url_for('reports.view_report', report_id=report_id))
            
        except Exception as e:
            logger.error(f"Error creating report: {str(e)}", exc_info=True)
            flash(f'An error occurred while creating the report: {str(e)}', 'error')
            return redirect(url_for('reports.new_report'))
    
    # Prepare data for the form
    try:
        # Get all GA4 properties
        properties = ga4_service.list_properties()
        
        # Get available plugins
        available_plugins = plugin_service.get_available_plugins()
        
        # Render report creation form
        return render_template('reports/new.html',
                              properties=properties,
                              plugins=available_plugins)
    
    except Exception as e:
        logger.error(f"Error loading report creation form: {str(e)}", exc_info=True)
        flash('An error occurred while loading the report creation form.', 'error')
        return redirect(url_for('reports.index'))

@reports_bp.route('/<int:report_id>')
@login_required
def view_report(report_id):
    """
    View a specific report.
    
    Args:
        report_id: The ID of the report to view
    """
    # Get report service
    report_service = get_service('report')
    if not report_service:
        flash('Report service is not available.', 'warning')
        return redirect(url_for('reports.index'))
    
    try:
        # Get report status
        report_status = report_service.get_report_status(report_id)
        
        if report_status.get('status') == 'not_found':
            flash(f'Report with ID {report_id} not found.', 'error')
            return redirect(url_for('reports.index'))
        
        # Get report data
        report_data = report_service.get_report_data(report_id)
        
        # Handle different report statuses
        if report_status.get('status') == 'completed':
            # Check if the report file exists
            file_path = report_status.get('file_path')
            if file_path and os.path.exists(file_path):
                # Determine file format
                file_ext = file_path.split('.')[-1].lower()
                
                # For HTML reports, embed the content
                if file_ext == 'html':
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            report_content = f.read()
                            return render_template('reports/view_html.html',
                                                  report=report_status,
                                                  report_content=report_content)
                    except Exception as e:
                        logger.error(f"Error reading HTML report file: {str(e)}", exc_info=True)
                        flash('An error occurred while reading the report file.', 'error')
                
                # For other formats (PDF, JSON), show download link
                return render_template('reports/view.html',
                                      report=report_status,
                                      report_data=report_data,
                                      file_format=file_ext)
            else:
                flash('Report file not found. It may have been deleted.', 'warning')
        
        # For pending or generating reports, show status page
        return render_template('reports/status.html',
                              report=report_status,
                              report_data=report_data)
    
    except Exception as e:
        logger.error(f"Error viewing report {report_id}: {str(e)}", exc_info=True)
        flash('An error occurred while loading the report.', 'error')
        return redirect(url_for('reports.index'))

@reports_bp.route('/<int:report_id>/download')
@login_required
def download_report(report_id):
    """
    Download a report file.
    
    Args:
        report_id: The ID of the report to download
    """
    # Get report service
    report_service = get_service('report')
    if not report_service:
        flash('Report service is not available.', 'warning')
        return redirect(url_for('reports.index'))
    
    try:
        # Get report status
        report_status = report_service.get_report_status(report_id)
        
        if report_status.get('status') == 'not_found':
            flash(f'Report with ID {report_id} not found.', 'error')
            return redirect(url_for('reports.index'))
        
        # Check if the report is completed and has a file
        if report_status.get('status') != 'completed':
            flash('Report is not ready for download yet.', 'warning')
            return redirect(url_for('reports.view_report', report_id=report_id))
        
        # Check if the file exists
        file_path = report_status.get('file_path')
        if not file_path or not os.path.exists(file_path):
            flash('Report file not found. It may have been deleted.', 'warning')
            return redirect(url_for('reports.view_report', report_id=report_id))
        
        # Determine file type and send the file
        file_ext = file_path.split('.')[-1].lower()
        
        # Create a user-friendly filename
        filename = f"{report_status.get('name', f'report_{report_id}').replace(' ', '_')}.{file_ext}"
        
        # Send the file
        return send_file(file_path, as_attachment=True, download_name=filename)
    
    except Exception as e:
        logger.error(f"Error downloading report {report_id}: {str(e)}", exc_info=True)
        flash('An error occurred while downloading the report.', 'error')
        return redirect(url_for('reports.view_report', report_id=report_id))

@reports_bp.route('/<int:report_id>/delete', methods=['POST'])
@login_required
def delete_report(report_id):
    """
    Delete a report.
    
    Args:
        report_id: The ID of the report to delete
    """
    # Get report service
    report_service = get_service('report')
    if not report_service:
        flash('Report service is not available.', 'warning')
        return redirect(url_for('reports.index'))
    
    try:
        # Delete the report
        result = report_service.delete_report(report_id)
        
        if result:
            flash('Report deleted successfully.', 'success')
        else:
            flash('Report not found or could not be deleted.', 'error')
        
        return redirect(url_for('reports.index'))
    
    except Exception as e:
        logger.error(f"Error deleting report {report_id}: {str(e)}", exc_info=True)
        flash(f'An error occurred while deleting the report: {str(e)}', 'error')
        return redirect(url_for('reports.index'))