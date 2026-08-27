"""
API Endpoints: Opportunities
Fully featured REST API for Opportunities including pagination, filtering, and deep validation.
"""
from flask import jsonify, request, current_app
from app.api import bp
from app.api.auth import api_login_required, api_role_required
from app.api.errors import bad_request, not_found, internal_server_error
from app.api.schemas import validate_opportunities_payload
from app.utils.storage import BaseStorage
from datetime import datetime

def get_storage():
    return BaseStorage(current_app.config['DATA_DIR'], 'opportunities')

@bp.route('/opportunities', methods=['GET'])
@api_login_required
def get_opportunities():
    """Retrieve opportunities with pagination and filtering."""
    try:
        storage = get_storage()
        records = storage.get_all_records()
        
        # Filtering
        status = request.args.get('status')
        if status:
            records = [r for r in records if r.get('status') == status]
            
        # Pagination
        try:
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 50))
        except ValueError:
            return bad_request('page and per_page must be integers.')
            
        start = (page - 1) * per_page
        end = start + per_page
        paginated = records[start:end]
        
        return jsonify({
            'meta': {
                'total': len(records),
                'page': page,
                'per_page': per_page,
                'total_pages': (len(records) + per_page - 1) // per_page
            },
            'data': paginated
        }), 200
    except Exception as e:
        return internal_server_error(e)

@bp.route('/opportunities/<record_id>', methods=['GET'])
@api_login_required
def get_single_opportunities(record_id):
    """Retrieve a single opportunities by ID."""
    try:
        storage = get_storage()
        record = storage.get_record(record_id)
        if not record: return not_found('Opportunities not found.')
        return jsonify({'data': record}), 200
    except Exception as e:
        return internal_server_error(e)

@bp.route('/opportunities', methods=['POST'])
@api_login_required
def create_opportunities():
    """Create a new opportunities record."""
    try:
        data = request.get_json() or {}
        is_valid, errors, sanitized = validate_opportunities_payload(data, is_update=False)
        if not is_valid: return bad_request(errors)
        
        storage = get_storage()
        new_id = storage.create_record(sanitized)
        sanitized['id'] = new_id
        return jsonify({'message': 'Opportunities created successfully.', 'data': sanitized}), 201
    except Exception as e:
        return internal_server_error(e)

@bp.route('/opportunities/<record_id>', methods=['PUT'])
@api_login_required
def update_opportunities(record_id):
    """Update an existing opportunities record."""
    try:
        storage = get_storage()
        if not storage.get_record(record_id): return not_found('Opportunities not found.')
        
        data = request.get_json() or {}
        is_valid, errors, sanitized = validate_opportunities_payload(data, is_update=True)
        if not is_valid: return bad_request(errors)
        
        storage.update_record(record_id, sanitized)
        return jsonify({'message': 'Opportunities updated successfully.', 'data': storage.get_record(record_id)}), 200
    except Exception as e:
        return internal_server_error(e)

@bp.route('/opportunities/<record_id>', methods=['DELETE'])
@api_login_required
@api_role_required('Admin', 'Manager')
def delete_opportunities(record_id):
    """Delete a opportunities record (Admin/Manager only)."""
    try:
        storage = get_storage()
        if storage.delete_record(record_id):
            return jsonify({'message': 'Opportunities deleted successfully.'}), 200
        return not_found('Opportunities not found.')
    except Exception as e:
        return internal_server_error(e)
