"""
API Endpoints: Customers
CRUD operations for Customer entities via REST.
"""
from flask import jsonify, request, current_app
from app.api import bp
from app.api.auth import api_login_required
from app.api.schemas import validate_customer_payload
from app.api.errors import bad_request, not_found
from app.utils.storage import BaseStorage

def get_storage():
    return BaseStorage(current_app.config['DATA_DIR'], 'customers')

@bp.route('/customers', methods=['GET'])
@api_login_required
def get_customers():
    """Retrieve all customers, with optional filtering."""
    storage = get_storage()
    records = storage.get_all_records()
    
    # Optional query params
    status = request.args.get('status')
    if status:
        records = [r for r in records if r.get('status') == status]
        
    return jsonify({
        'meta': {
            'total': len(records),
            'filters_applied': {'status': status} if status else {}
        },
        'data': records
    }), 200

@bp.route('/customers/<record_id>', methods=['GET'])
@api_login_required
def get_customer(record_id):
    """Retrieve a single customer by ID."""
    storage = get_storage()
    record = storage.get_record(record_id)
    if not record:
        return not_found(f'Customer with ID {record_id} not found.')
    return jsonify({'data': record}), 200

@bp.route('/customers', methods=['POST'])
@api_login_required
def create_customer_api():
    """Create a new customer."""
    data = request.get_json() or {}
    is_valid, errors, sanitized = validate_customer_payload(data, is_update=False)
    if not is_valid:
        return bad_request(errors)
        
    storage = get_storage()
    new_id = storage.create_record(sanitized)
    sanitized['id'] = new_id
    
    return jsonify({
        'message': 'Customer created successfully.',
        'data': sanitized
    }), 201

@bp.route('/customers/<record_id>', methods=['PUT'])
@api_login_required
def update_customer_api(record_id):
    """Update an existing customer."""
    storage = get_storage()
    if not storage.get_record(record_id):
        return not_found(f'Customer with ID {record_id} not found.')
        
    data = request.get_json() or {}
    is_valid, errors, sanitized = validate_customer_payload(data, is_update=True)
    if not is_valid:
        return bad_request(errors)
        
    storage.update_record(record_id, sanitized)
    updated_record = storage.get_record(record_id)
    
    return jsonify({
        'message': 'Customer updated successfully.',
        'data': updated_record
    }), 200

@bp.route('/customers/<record_id>', methods=['DELETE'])
@api_login_required
def delete_customer_api(record_id):
    """Delete a customer."""
    storage = get_storage()
    if storage.delete_record(record_id):
        return jsonify({'message': 'Customer deleted successfully.'}), 200
    return not_found(f'Customer with ID {record_id} not found.')
