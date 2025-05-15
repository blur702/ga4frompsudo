"""
Dashboard controller for handling dashboard views and operations.
"""

import logging
from flask import Blueprint, render_template, flash, redirect, url_for, request, current_app

from app.services import get_service
from app.controllers.auth_controller import login_required

logger = logging.getLogger(__name__)

# Create blueprint
dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    """
    Display the main dashboard page with overview information.
    """
    # Get required services
    ga4_service = get_service('ga4')
    plugin_service = get_service('plugin')
    
    if not ga4_service or not ga4_service.is_available():
        flash('Google Analytics service is not available. Check your credentials.', 'warning')
        return render_template('dashboard/error.html', 
                              title='Service Unavailable',
                              message='The Google Analytics service is currently unavailable.')
    
    try:
        # Get current user's properties
        properties = ga4_service.list_properties()
        
        # Get active users count for each property
        active_users = {}
        for prop in properties:
            property_id = prop.get('name', '').split('/')[-1]  # Extract ID from "properties/123456"
            if property_id:
                active_users[property_id] = ga4_service.get_realtime_users(property_id)
        
        # Get engagement metrics plugin if available
        engagement_plugin = None
        if plugin_service:
            engagement_plugin = plugin_service.get_plugin_instance('engagement_metrics')
        
        # Render dashboard template with data
        return render_template('dashboard/index.html',
                              properties=properties,
                              active_users=active_users,
                              engagement_plugin=engagement_plugin is not None)
                              
    except Exception as e:
        logger.error(f"Error loading dashboard: {str(e)}", exc_info=True)
        flash('An error occurred while loading the dashboard.', 'error')
        return render_template('dashboard/error.html', 
                              title='Dashboard Error',
                              message='An error occurred while loading the dashboard data.')

@dashboard_bp.route('/property/<property_id>')
@login_required
def property_dashboard(property_id):
    """
    Display dashboard for a specific property.
    
    Args:
        property_id: The GA4 property ID
    """
    # Get required services
    ga4_service = get_service('ga4')
    
    if not ga4_service or not ga4_service.is_available():
        flash('Google Analytics service is not available. Check your credentials.', 'warning')
        return redirect(url_for('dashboard.index'))
    
    try:
        # Get property details
        property_details = ga4_service.get_property(property_id)
        if not property_details:
            flash(f'Property with ID {property_id} not found.', 'error')
            return redirect(url_for('dashboard.index'))
        
        # Get property streams (websites, apps)
        streams = ga4_service.list_streams(property_id)
        
        # Get basic traffic metrics
        traffic_data = ga4_service.get_traffic_report(
            property_id=property_id,
            date_range='last30days'
        )
        
        # Format the data for display
        formatted_traffic = ga4_service.format_report_data(traffic_data)
        
        # Get active users
        active_users = ga4_service.get_realtime_users(property_id)
        
        # Render property dashboard
        return render_template('dashboard/property.html',
                              property=property_details,
                              streams=streams,
                              traffic_data=formatted_traffic,
                              active_users=active_users)
                              
    except Exception as e:
        logger.error(f"Error loading property dashboard for {property_id}: {str(e)}", exc_info=True)
        flash(f'An error occurred while loading data for property {property_id}.', 'error')
        return redirect(url_for('dashboard.index'))

@dashboard_bp.route('/analytics')
@login_required
def analytics():
    """
    Display consolidated analytics dashboard with metrics from all properties.
    """
    # This is a placeholder for a consolidated analytics view
    
    return render_template('dashboard/analytics.html',
                          title='Analytics Dashboard',
                          message='Consolidated analytics dashboard coming soon!')

@dashboard_bp.route('/plugins')
@login_required
def plugins():
    """
    Display and manage available analytics plugins.
    """
    # Get plugin service
    plugin_service = get_service('plugin')
    if not plugin_service:
        flash('Plugin service is not available.', 'warning')
        return redirect(url_for('dashboard.index'))
    
    try:
        # Get all available plugins
        available_plugins = plugin_service.get_available_plugins()
        
        # Render plugins page
        return render_template('dashboard/plugins.html',
                              plugins=available_plugins)
    
    except Exception as e:
        logger.error(f"Error loading plugins page: {str(e)}", exc_info=True)
        flash('An error occurred while loading plugins information.', 'error')
        return redirect(url_for('dashboard.index'))