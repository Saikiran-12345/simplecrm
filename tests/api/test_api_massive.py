import pytest
from app.utils.storage import BaseStorage
from werkzeug.security import generate_password_hash

@pytest.fixture
def api_client(client, app):
    with app.app_context():
        storage = BaseStorage(app.config['DATA_DIR'], 'users')
        storage.create_record({
            'username': 'admin_api',
            'password_hash': generate_password_hash('password123'),
            'role': 'Admin',
            'status': 'Active'
        })
    return client

@pytest.fixture
def api_headers(api_client):
    auth_resp = api_client.post('/api/v1/auth/token', json={'username': 'admin_api', 'password': 'password123'})
    token = auth_resp.get_json()['token']
    return {'Authorization': f'Bearer {token}'}

# Parameterized test for every module
MODULES = ['customers', 'leads', 'opportunities', 'products', 'sales', 'invoices', 'payments', 'tasks', 'followups', 'notes', 'employees']

@pytest.mark.parametrize('module', MODULES)
def test_api_crud_lifecycle(api_client, api_headers, module):
    # Create
    create_resp = api_client.post(f'/api/v1/{module}', json={'test_field': 'value', 'first_name': 'API Test'}, headers=api_headers)
    assert create_resp.status_code == 201
    record_id = create_resp.get_json()['data']['id']
    
    # Read All
    get_resp = api_client.get(f'/api/v1/{module}', headers=api_headers)
    assert get_resp.status_code == 200
    
    # Read Single
    get_single = api_client.get(f'/api/v1/{module}/{record_id}', headers=api_headers)
    assert get_single.status_code == 200
    
    # Update
    update_resp = api_client.put(f'/api/v1/{module}/{record_id}', json={'test_field': 'updated'}, headers=api_headers)
    assert update_resp.status_code == 200
    
    # Delete
    delete_resp = api_client.delete(f'/api/v1/{module}/{record_id}', headers=api_headers)
    assert delete_resp.status_code == 200
