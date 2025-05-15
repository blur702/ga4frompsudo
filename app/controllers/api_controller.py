"""
API controller for handling API endpoints.
"""

import logging
from flask import Blueprint, request, jsonify, g, current_app
from functools import wraps

from app.services import get_service

logger = logging.getLogger(__name__)

# Create blueprint
api_bp = Blueprint('api', __name__)

# API authentication decorator
def require_api_token(required_scope='read'):
    """
    Decorator to enforce API token authentication.
    
    Args:
        required_scope: The required scope for the endpoint
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(*args, **kwargs):
            # Get auth service
            auth_service = get_service('auth')
            if not auth_service:
                return jsonify({'error': 'Authentication service unavailable'}), 503
            
            # Get token from header
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({'error': 'Missing or invalid Authorization header'}), 401
            
            # Extract token
            token = auth_header.split(' ')[1]
            
            # Validate token
            valid, payload = auth_service.validate_api_token(token)
            if not valid:
                return jsonify({'error': 'Invalid or expired token'}), 401
            
            # Check scope
            if not auth_service.check_token_scope(payload, required_scope):
                return jsonify({'error': f'Token missing required scope: {required_scope}'}), 403
            
            # Store user ID in g object for use in the view
            g.user_id = payload.get('sub')
            
            # Call the view function
            return view_func(*args, **kwargs)
        return wrapped_view
    return decorator

@api_bp.route('/properties', methods=['GET'])
@require_api_token(required_scope='read')
def get_properties():
    """
    API endpoint to get all GA4 properties.
    """
    # Get GA4 service
    ga4_service = get_service('ga4')
    if not ga4_service or not ga4_service.is_available():
        return jsonify({'error': 'Google Analytics service unavailable'}), 503
    
    try:
        # Get properties
        properties = ga4_service.list_properties()
        
        # Format the response
        formatted_properties = []
        for prop in properties:
            # Extract relevant fields
            property_id = prop.get('name', '').split('/')[-1]
            formatted_properties.append({
                'id': property_id,
                'displayName': prop.get('displayName', ''),
                'createTime': prop.get('createTime', ''),
                'updateTime': prop.get('updateTime', '')
            })
        
        return jsonify({'properties': formatted_properties})
    
    except Exception as e:
        logger.error(f"API error getting properties: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@api_bp.route('/properties/<property_id>/metrics', methods=['GET'])
@require_api_token(required_scope='read')
def get_property_metrics(property_id):
    """
    API endpoint to get metrics for a specific property.
    
    Args:
        property_id: The GA4 property ID
    """
    # Get GA4 service
    ga4_service = get_service('ga4')
    if not ga4_service or not ga4_service.is_available():
        return jsonify({'error': 'Google Analytics service unavailable'}), 503
    
    try:
        # Get query parameters
        metrics = request.args.get('metrics', 'totalUsers,newUsers,screenPageViews,sessions,engagementRate').split(',')
        dimensions = request.args.get('dimensions', 'date').split(',')
        date_range = request.args.get('dateRange', 'last30days')
        
        # Run the report
        report = ga4_service.run_report(
            property_id=property_id,
            start_date=date_range,
            end_date='today',
            metrics=metrics,
            dimensions=dimensions
        )
        
        # Format the data
        formatted_data = ga4_service.format_report_data(report)
        
        return jsonify({
            'property_id': property_id,
            'date_range': date_range,
            'metrics': metrics,
            'dimensions': dimensions,
            'data': formatted_data
        })
    
    except Exception as e:
        logger.error(f"API error getting metrics for property {property_id}: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@api_bp.route('/reports', methods=['GET'])
@require_api_token(required_scope='read')
def get_reports():
    """
    API endpoint to get all reports.
    """
    # Get report service
    report_service = get_service('report')
    if not report_service:
        return jsonify({'error': 'Report service unavailable'}), 503
    
    try:
        # Get query parameters
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        report_type = request.args.get('type')
        
        # Get reports
        reports = report_service.list_reports(limit=limit, offset=offset, report_type=report_type)
        
        return jsonify({'reports': reports})
    
    except Exception as e:
        logger.error(f"API error getting reports: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@api_bp.route('/reports/<int:report_id>', methods=['GET'])
@require_api_token(required_scope='read')
def get_report(report_id):
    """
    API endpoint to get a specific report.
    
    Args:
        report_id: The ID of the report to get
    """
    # Get report service
    report_service = get_service('report')
    if not report_service:
        return jsonify({'error': 'Report service unavailable'}), 503
    
    try:
        # Get report status
        report_status = report_service.get_report_status(report_id)
        
        if report_status.get('status') == 'not_found':
            return jsonify({'error': f'Report with ID {report_id} not found.'}), 404
        
        # Get report data
        include_data = request.args.get('includeData', 'false').lower() == 'true'
        response = {'report': report_status}
        
        if include_data:
            report_data = report_service.get_report_data(report_id)
            response['data'] = report_data
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"API error getting report {report_id}: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@api_bp.route('/reports', methods=['POST'])
@require_api_token(required_scope='write')
def create_report():
    """
    API endpoint to create a new report.
    """
    # Get required services
    report_service = get_service('report')
    
    if not report_service:
        return jsonify({'error': 'Report service unavailable'}), 503
    
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Missing request body'}), 400
        
        # Extract parameters
        report_name = data.get('report_name')
        report_type = data.get('report_type')
        parameters = data.get('parameters', {})
        
        # Validate inputs
        if not report_name or not report_type:
            return jsonify({'error': 'Report name and type are required.'}), 400
        
        # Create the report
        report_id = report_service.create_report(
            report_name=report_name,
            report_type=report_type,
            parameters=parameters
        )
        
        # Generate the report if requested
        generate = data.get('generate', False)
        if generate:
            format_type = data.get('format_type', 'json')
            report_path = report_service.generate_report(report_id, format_type=format_type)
            return jsonify({
                'id': report_id,
                'status': 'completed' if report_path else 'failed',
                'file_path': report_path
            })
        
        return jsonify({'id': report_id, 'status': 'pending'})
    
    except Exception as e:
        logger.error(f"API error creating report: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@api_bp.route('/reports/<int:report_id>', methods=['DELETE'])
@require_api_token(required_scope='write')
def delete_report(report_id):
    """
    API endpoint to delete a report.
    
    Args:
        report_id: The ID of the report to delete
    """
    # Get report service
    report_service = get_service('report')
    if not report_service:
        return jsonify({'error': 'Report service unavailable'}), 503
    
    try:
        # Delete the report
        result = report_service.delete_report(report_id)
        
        if result:
            return jsonify({'success': True, 'message': 'Report deleted successfully.'}), 200
        else:
            return jsonify({'error': 'Report not found or could not be deleted.'}), 404
    
    except Exception as e:
        logger.error(f"API error deleting report {report_id}: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@api_bp.route('/tokens', methods=['POST'])
@require_api_token(required_scope='admin')
def create_api_token():
    """
    API endpoint to create a new API token.
    Requires admin scope to generate tokens.
    """
    # Get auth service
    auth_service = get_service('auth')
    if not auth_service:
        return jsonify({'error': 'Authentication service unavailable'}), 503
    
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Missing request body'}), 400
        
        # Extract parameters
        user_id = data.get('user_id')
        scopes = data.get('scopes', ['read'])
        
        # Validate inputs
        if not user_id:
            return jsonify({'error': 'User ID is required.'}), 400
        
        # Generate token
        token = auth_service.generate_api_token(user_id, scopes)
        
        return jsonify({'token': token, 'scopes': scopes, 'user_id': user_id})
    
    except Exception as e:
        logger.error(f"API error creating token: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500