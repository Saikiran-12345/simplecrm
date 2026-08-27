modules = ['leads', 'opportunities', 'products', 'sales', 'invoices', 'payments', 'tasks', 'notes', 'employees']

for mod in modules:
    with open(f'app/api/{mod}.py', 'w', encoding='utf-8') as f:
        f.write(f"""\"\"\"
API Endpoints: {mod.capitalize()}
CRUD operations for {mod.capitalize()} entities via REST.
\"\"\"
from flask import jsonify, request, current_app
from app.api import bp
from app.api.auth import api_login_required
from app.api.errors import bad_request, not_found
from app.utils.storage import BaseStorage

def get_storage():
    return BaseStorage(current_app.config['DATA_DIR'], '{mod}')

@bp.route('/{mod}', methods=['GET'])
@api_login_required
def get_{mod}():
    storage = get_storage()
    records = storage.get_all_records()
    return jsonify({{'meta': {{'total': len(records)}}, 'data': records}}), 200

@bp.route('/{mod}/<record_id>', methods=['GET'])
@api_login_required
def get_single_{mod}(record_id):
    storage = get_storage()
    record = storage.get_record(record_id)
    if not record: return not_found('{mod.capitalize()} not found.')
    return jsonify({{'data': record}}), 200

@bp.route('/{mod}', methods=['POST'])
@api_login_required
def create_{mod}():
    data = request.get_json() or {{}}
    storage = get_storage()
    new_id = storage.create_record(data)
    data['id'] = new_id
    return jsonify({{'message': '{mod.capitalize()} created.', 'data': data}}), 201

@bp.route('/{mod}/<record_id>', methods=['PUT'])
@api_login_required
def update_{mod}(record_id):
    storage = get_storage()
    if not storage.get_record(record_id): return not_found('{mod.capitalize()} not found.')
    data = request.get_json() or {{}}
    storage.update_record(record_id, data)
    return jsonify({{'message': '{mod.capitalize()} updated.', 'data': storage.get_record(record_id)}}), 200

@bp.route('/{mod}/<record_id>', methods=['DELETE'])
@api_login_required
def delete_{mod}(record_id):
    storage = get_storage()
    if storage.delete_record(record_id):
        return jsonify({{'message': '{mod.capitalize()} deleted.'}}), 200
    return not_found('{mod.capitalize()} not found.')
""")

