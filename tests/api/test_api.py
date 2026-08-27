import pytest
from app.utils.storage import BaseStorage
from werkzeug.security import generate_password_hash

@pytest.fixture
def api_client(client, app):
    with app.app_context():
        storage = BaseStorage(app.config['DATA_DIR'], 'users')
        storage.create_record({
            'username': 'api_user',
            'password_hash': generate_password_hash('password123'),
            'role': 'Admin',
            'status': 'Active'
        })
    return client

def test_api_auth_token(api_client):
    response = api_client.post('/api/v1/auth/token', json={
        'username': 'api_user',
        'password': 'password123'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert 'token' in data

def test_api_customers(api_client):
    # 1. Get Token
    auth_resp = api_client.post('/api/v1/auth/token', json={'username': 'api_user', 'password': 'password123'})
    token = auth_resp.get_json()['token']
    headers = {'Authorization': f'Bearer {token}'}

    # 2. Create Customer
    create_resp = api_client.post('/api/v1/customers', json={
        'first_name': 'API',
        'last_name': 'Tester',
        'email': 'api@test.com'
    }, headers=headers)
    assert create_resp.status_code == 201
    c_id = create_resp.get_json()['data']['id']

    # 3. Get Customers
    get_resp = api_client.get('/api/v1/customers', headers=headers)
    assert get_resp.status_code == 200
    assert len(get_resp.get_json()['data']) > 0

    # 4. Update Customer
    update_resp = api_client.put(f'/api/v1/customers/{c_id}', json={
        'first_name': 'API Updated'
    }, headers=headers)
    assert update_resp.status_code == 200
    assert update_resp.get_json()['data']['first_name'] == 'API Updated'

    # 5. Delete Customer
    delete_resp = api_client.delete(f'/api/v1/customers/{c_id}', headers=headers)
    assert delete_resp.status_code == 200
