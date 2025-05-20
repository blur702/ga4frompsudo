import os
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, redirect, url_for, request, session, flash, jsonify, send_file
from flask_migrate import Migrate
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.utils import secure_filename

from modules.models import db, Property, AnalyticsData, Setting, PropertySelectionSet, ReportTemplate
from modules.auth import create_flow, save_credentials, clear_credentials, build_credentials, login_required, get_user_info, revoke_token, is_logged_in
from modules.ga_api import sync_ga4_properties, get_analytics_report, fetch_and_store_analytics_report, batch_fetch_analytics_data
from modules.ga4_metadata_service import update_ga4_metadata, get_metrics_by_category, get_dimensions_by_category
from modules.reporting.common import get_date_range_for_form, format_date_for_display
from modules.reporting.url_analytics import generate_url_analytics_report
from modules.reporting.property_aggregation import generate_property_aggregation_report
from modules.reporting.common_pdf import generate_report_pdf

# Create a Flask application
app = Flask(__name__)

# Load configuration
app.config.from_object('config.Config')

# Security settings (simplified version without Flask-Talisman and Flask-WTF)
if not app.debug and not app.testing:
    # Set secure cookie settings
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['REMEMBER_COOKIE_SECURE'] = True
    app.config['REMEMBER_COOKIE_HTTPONLY'] = True

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join('logs', 'app.log'))
    ]
)

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = app.config.get('DATABASE_URI', 'sqlite:///ga4_dashboard.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Configure migrations
migrate = Migrate(app, db)

# Configure session
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)

# Configure proxy fix for proper IP handling behind reverse proxies
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# Ensure directories exist
os.makedirs('logs', exist_ok=True)
os.makedirs('uploads', exist_ok=True)
os.makedirs('reports', exist_ok=True)

# Create database tables if they don't exist
with app.app_context():
    db.create_all()

# Include Date Utils
from datetime import datetime

@app.context_processor
def inject_now():
    return {'now': datetime.now()}

# Routes
@app.route('/')
def index():
    """Home page route."""
    if not is_logged_in():
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))

@app.route('/login')
def login():
    """Login page route."""
    # Check if user is already logged in via OAuth or API key
    if is_logged_in():
        return redirect(url_for('dashboard'))
        
    # Check if API key is configured when OAuth fallback is enabled
    api_key_configured = False
    if app.config.get('OAUTH_FALLBACK_ENABLED', False):
        api_key = Setting.get_value('google_api_key')
        api_key_configured = bool(api_key)
    
    return render_template('login.html', api_key_configured=api_key_configured)

@app.route('/authorize')
def authorize():
    """Route to initiate OAuth flow."""
    flow = create_flow()
    
    # If flow creation failed (e.g., client ID not configured)
    if not flow:
        if app.config.get('OAUTH_FALLBACK_ENABLED', False):
            # Check if API key is configured
            api_key = Setting.get_value('google_api_key')
            if api_key:
                flash("Using API key authentication instead of OAuth.", "info")
                return redirect(url_for('dashboard'))
            else:
                flash("OAuth is not configured and no API key is available. Please configure at least one authentication method.", "error")
                return redirect(url_for('settings'))
        else:
            flash("OAuth authentication is not properly configured.", "error")
            return redirect(url_for('login'))
    
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    session['state'] = state
    return redirect(authorization_url)

@app.route('/oauth2callback')
def oauth2callback():
    """OAuth callback route."""
    state = session.get('state')
    if not state or state != request.args.get('state'):
        return redirect(url_for('login'))
    
    flow = create_flow()
    if not flow:
        flash("OAuth flow could not be created. Check your configuration.", "error")
        return redirect(url_for('login'))
        
    try:
        flow.fetch_token(authorization_response=request.url)
    except Exception as e:
        app.logger.error(f"Error fetching OAuth token: {e}")
        flash(f"Authentication error: {str(e)}", "error")
        return redirect(url_for('login'))
    
    credentials = flow.credentials
    save_credentials(credentials)
    
    # Sync GA4 properties after successful login
    sync_ga4_properties()
    
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    """Logout route."""
    revoke_token()
    clear_credentials()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard page route."""
    user_info = get_user_info()
    properties = Property.query.order_by(Property.display_name).all()
    
    # Get date range for form
    start_date, end_date = get_date_range_for_form(30)
    
    # Check authentication method
    using_api_key = False
    if not build_credentials() and app.config.get('OAUTH_FALLBACK_ENABLED', False):
        api_key = Setting.get_value('google_api_key')
        using_api_key = bool(api_key)
    
    return render_template(
        'dashboard.html',
        user_info=user_info,
        properties=properties,
        start_date=start_date,
        end_date=end_date,
        using_api_key=using_api_key
    )

@app.route('/properties')
@login_required
def properties():
    """Properties management page route."""
    properties = Property.query.order_by(Property.display_name).all()
    return render_template('properties.html', properties=properties)

@app.route('/properties/sync', methods=['POST'])
@login_required
def sync_properties():
    """Route to sync GA4 properties."""
    properties = sync_ga4_properties()
    flash(f"Successfully synced {len(properties)} properties.", "success")
    return redirect(url_for('properties'))

@app.route('/properties/<int:property_id>/toggle_exclude', methods=['POST'])
@login_required
def toggle_property_exclude(property_id):
    """Route to toggle property exclusion from global reports."""
    property = Property.query.get_or_404(property_id)
    property.exclude_from_global_reports = not property.exclude_from_global_reports
    db.session.commit()
    
    return jsonify({
        'success': True,
        'property_id': property_id,
        'excluded': property.exclude_from_global_reports
    })

@app.route('/properties/<int:property_id>/update_metadata', methods=['POST'])
@login_required
def update_property_metadata(property_id):
    """Route to update GA4 metadata for a property."""
    property = Property.query.get_or_404(property_id)
    
    success = update_ga4_metadata(property.ga_property_id)
    if success:
        flash(f"Successfully updated metadata for {property.display_name}.", "success")
    else:
        flash(f"Failed to update metadata for {property.display_name}.", "error")
    
    return redirect(url_for('properties'))

@app.route('/reports')
@login_required
def reports():
    """Reports page route."""
    properties = Property.query.order_by(Property.display_name).all()
    selection_sets = PropertySelectionSet.query.order_by(PropertySelectionSet.name).all()
    report_templates = ReportTemplate.query.order_by(ReportTemplate.name).all()
    
    # Get date range for form
    start_date, end_date = get_date_range_for_form(30)
    
    # Get metrics and dimensions
    metrics_by_category = get_metrics_by_category()
    dimensions_by_category = get_dimensions_by_category()
    
    return render_template(
        'reports.html',
        properties=properties,
        selection_sets=selection_sets,
        report_templates=report_templates,
        start_date=start_date,
        end_date=end_date,
        metrics_by_category=metrics_by_category,
        dimensions_by_category=dimensions_by_category
    )

@app.route('/reports/url_analytics', methods=['GET', 'POST'])
@login_required
def url_analytics():
    """URL analytics report page route."""
    if request.method == 'POST':
        url = request.form.get('url')
        property_id = request.form.get('property_id')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        metrics = request.form.getlist('metrics')
        dimensions = request.form.getlist('dimensions')
        
        # Validate inputs
        if not url or not property_id or not start_date or not end_date or not metrics:
            flash("Please fill in all required fields.", "error")
            return redirect(url_for('reports'))
        
        # Generate report
        report = generate_url_analytics_report(
            url, start_date, end_date, property_id, metrics, dimensions
        )
        
        if not report:
            flash("Failed to generate report. Please try again.", "error")
            return redirect(url_for('reports'))
        
        # Store report in session for PDF generation
        session['url_analytics_report'] = report
        
        return render_template(
            'reports/url_analytics.html',
            report=report,
            format_date=format_date_for_display
        )
    
    return redirect(url_for('reports'))

@app.route('/reports/property_aggregation', methods=['GET', 'POST'])
@login_required
def property_aggregation():
    """Property aggregation report page route."""
    if request.method == 'POST':
        property_ids = request.form.getlist('property_ids')
        selection_set_id = request.form.get('selection_set_id')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        metrics = request.form.getlist('metrics')
        dimensions = request.form.getlist('dimensions')
        
        # If selection set is provided, use its property IDs
        if selection_set_id:
            selection_set = PropertySelectionSet.query.get(selection_set_id)
            if selection_set:
                property_ids = selection_set.get_property_ids()
        
        # Validate inputs
        if not property_ids or not start_date or not end_date or not metrics:
            flash("Please fill in all required fields.", "error")
            return redirect(url_for('reports'))
        
        # Generate report
        report = generate_property_aggregation_report(
            property_ids, start_date, end_date, metrics, dimensions
        )
        
        if not report:
            flash("Failed to generate report. Please try again.", "error")
            return redirect(url_for('reports'))
        
        # Store report in session for PDF generation
        session['property_aggregation_report'] = report
        
        return render_template(
            'reports/property_aggregation.html',
            report=report,
            format_date=format_date_for_display
        )
    
    return redirect(url_for('reports'))

@app.route('/reports/url_analytics/pdf')
@login_required
def url_analytics_pdf():
    """Route to generate PDF for URL analytics report."""
    report = session.get('url_analytics_report')
    if not report:
        flash("Report not found. Please generate the report again.", "error")
        return redirect(url_for('reports'))
    
    # Generate PDF
    output_path = os.path.join('reports', f"url_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
    pdf_path = generate_report_pdf(
        report, 'url_analytics', output_path,
        include_summary=True,
        include_url_overview=True,
        include_screenshot=True
    )
    
    if not pdf_path:
        flash("Failed to generate PDF. Please try again.", "error")
        return redirect(url_for('url_analytics'))
    
    return send_file(pdf_path, as_attachment=True, download_name=os.path.basename(pdf_path))

@app.route('/reports/property_aggregation/pdf')
@login_required
def property_aggregation_pdf():
    """Route to generate PDF for property aggregation report."""
    report = session.get('property_aggregation_report')
    if not report:
        flash("Report not found. Please generate the report again.", "error")
        return redirect(url_for('reports'))
    
    # Generate PDF
    output_path = os.path.join('reports', f"property_aggregation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
    pdf_path = generate_report_pdf(
        report, 'property_aggregation', output_path,
        include_summary=True
    )
    
    if not pdf_path:
        flash("Failed to generate PDF. Please try again.", "error")
        return redirect(url_for('property_aggregation'))
    
    return send_file(pdf_path, as_attachment=True, download_name=os.path.basename(pdf_path))

@app.route('/selection_sets', methods=['GET', 'POST'])
@login_required
def selection_sets():
    """Property selection sets management page route."""
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        property_ids = request.form.getlist('property_ids')
        
        # Validate inputs
        if not name or not property_ids:
            flash("Please fill in all required fields.", "error")
            return redirect(url_for('selection_sets'))
        
        # Create selection set
        selection_set = PropertySelectionSet(
            name=name,
            description=description
        )
        selection_set.set_property_ids(property_ids)
        
        db.session.add(selection_set)
        db.session.commit()
        
        flash(f"Successfully created selection set '{name}'.", "success")
        return redirect(url_for('selection_sets'))
    
    properties = Property.query.order_by(Property.display_name).all()
    selection_sets = PropertySelectionSet.query.order_by(PropertySelectionSet.name).all()
    
    return render_template(
        'selection_sets.html',
        properties=properties,
        selection_sets=selection_sets
    )

@app.route('/selection_sets/<int:set_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_selection_set(set_id):
    """Route to edit a property selection set."""
    selection_set = PropertySelectionSet.query.get_or_404(set_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        property_ids = request.form.getlist('property_ids')
        
        # Validate inputs
        if not name or not property_ids:
            flash("Please fill in all required fields.", "error")
            return redirect(url_for('edit_selection_set', set_id=set_id))
        
        # Update selection set
        selection_set.name = name
        selection_set.description = description
        selection_set.set_property_ids(property_ids)
        
        db.session.commit()
        
        flash(f"Successfully updated selection set '{name}'.", "success")
        return redirect(url_for('selection_sets'))
    
    properties = Property.query.order_by(Property.display_name).all()
    
    return render_template(
        'edit_selection_set.html',
        selection_set=selection_set,
        properties=properties,
        selected_property_ids=selection_set.get_property_ids()
    )

@app.route('/selection_sets/<int:set_id>/delete', methods=['POST'])
@login_required
def delete_selection_set(set_id):
    """Route to delete a property selection set."""
    selection_set = PropertySelectionSet.query.get_or_404(set_id)
    
    db.session.delete(selection_set)
    db.session.commit()
    
    flash(f"Successfully deleted selection set '{selection_set.name}'.", "success")
    return redirect(url_for('selection_sets'))

@app.route('/settings')
def settings():
    """Settings page route."""
    settings = Setting.query.order_by(Setting.key).all()
    
    # Check if the user is logged in
    is_authenticated = is_logged_in()
    
    return render_template('settings.html', settings=settings, is_authenticated=is_authenticated)

@app.route('/settings/update', methods=['POST'])
@login_required
def update_settings():
    """Route to update settings."""
    for key, value in request.form.items():
        if key.startswith('setting_'):
            setting_key = key[8:]  # Remove 'setting_' prefix
            
            # Skip empty API key to preserve existing value
            if setting_key == 'google_api_key' and not value:
                continue
                
            # Validate API key format if provided
            if setting_key == 'google_api_key' and value:
                # Google API keys are typically around 39 characters
                if len(value) < 20:
                    flash("The API key appears to be too short. Please check your API key.", "error")
                    return redirect(url_for('settings'))
                
                # Basic format validation
                if not all(c.isalnum() or c in '-_' for c in value):
                    flash("The API key contains invalid characters. API keys should only contain letters, numbers, hyphens, and underscores.", "error")
                    return redirect(url_for('settings'))
                
            # Determine if this setting should be encrypted
            is_encrypted = False
            if setting_key == 'google_api_key':
                is_encrypted = True
                
            # Get description based on setting key
            description = None
            if setting_key == 'google_api_key':
                description = 'Google API key for authentication'
            elif setting_key == 'api_request_timeout':
                description = 'Maximum time to wait for API responses (seconds)'
            elif setting_key == 'max_concurrent_requests':
                description = 'Maximum number of concurrent API requests'
                
            # Use the set_value class method to handle encryption
            Setting.set_value(setting_key, value, description, is_encrypted)
            
            # Log the update (without the actual value for sensitive data)
            if is_encrypted:
                app.logger.info(f"Updated encrypted setting: {setting_key}")
            else:
                app.logger.info(f"Updated setting: {setting_key} = {value}")
    
    flash("Settings updated successfully.", "success")
    return redirect(url_for('settings'))

@app.errorhandler(404)
def page_not_found(e):
    """404 error handler."""
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(e):
    """500 error handler."""
    app.logger.error(f"Server error: {e}")
    
    # Log the traceback for debugging
    import traceback
    app.logger.error(traceback.format_exc())
    
    # Check if the error is related to database or settings
    error_message = str(e).lower()
    if 'database' in error_message or 'sql' in error_message:
        # Database-related error
        return render_template('errors/500.html',
                              error_type="Database Error",
                              error_details="There was an issue with the database. Please check your database configuration.",
                              show_settings_link=True), 500
    elif 'setting' in error_message or 'config' in error_message or 'api' in error_message:
        # Settings or API-related error
        return render_template('errors/500.html',
                              error_type="Configuration Error",
                              error_details="There was an issue with your application configuration. Please check your settings.",
                              show_settings_link=True), 500
    else:
        # Generic error
        return render_template('errors/500.html'), 500

if __name__ == '__main__':
    # Get host and port from environment variables or use defaults
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_PORT', 5003))  # Using 5003 to avoid conflicts with other processes
    debug_mode = app.config.get('DEBUG', False)
    
    # Always use http for local development since we don't have SSL certificates configured
    protocol = 'http'
    
    # Print the complete URL to the console with clear formatting
    url_message = f"""
\033[1;32m{'*' * 70}
*
*  SYSTEM INITIALIZATION COMPLETE
*  GA4 Dashboard is running at: {protocol}://{host}:{port}
*
{'*' * 70}\033[0m
"""
    print(url_message)
    
    # Import time for a small delay to ensure message visibility
    import time
    time.sleep(0.5)
    
    # Run the application
    app.run(host=host, port=port, debug=debug_mode)
