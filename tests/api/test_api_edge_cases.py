import pytest
from app.utils.storage import BaseStorage
from werkzeug.security import generate_password_hash
import jwt
from datetime import datetime, timedelta

@pytest.fixture
def api_client(client, app):
    with app.app_context():
        storage = BaseStorage(app.config['DATA_DIR'], 'users')
        storage.create_record({
            'username': 'edge_user',
            'password_hash': generate_password_hash('pass'),
            'role': 'User',
            'status': 'Active'
        })
    return client

def test_api_unauthorized_no_token(api_client):
    response = api_client.get('/api/v1/customers')
    assert response.status_code == 401

def test_api_unauthorized_bad_token(api_client):
    response = api_client.get('/api/v1/customers', headers={'Authorization': 'Bearer garbage.token.here'})
    assert response.status_code == 401
    
def test_api_expired_token(api_client, app):
    payload = {
        'user_id': '123',
        'role': 'Admin',
        'exp': datetime.utcnow() - timedelta(seconds=3600), # EXPIRED
        'iat': datetime.utcnow()
    }
    with app.app_context():
        token = jwt.encode(payload, app.config.get('SECRET_KEY', 'fallback_secret'), algorithm='HS256')
        
    response = api_client.get('/api/v1/customers', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 401

def test_api_forbidden_role(api_client, app):
    # Log in as 'User' role
    auth_resp = api_client.post('/api/v1/auth/token', json={'username': 'edge_user', 'password': 'pass'})
    token = auth_resp.get_json()['token']
    
    # Try to delete (requires Admin/Manager)
    resp = api_client.delete('/api/v1/customers/fake_id', headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 403

def test_api_not_found(api_client):
    auth_resp = api_client.post('/api/v1/auth/token', json={'username': 'edge_user', 'password': 'pass'})
    token = auth_resp.get_json()['token']
    
    resp = api_client.get('/api/v1/customers/invalid_12345', headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 404

def test_api_bad_pagination(api_client):
    auth_resp = api_client.post('/api/v1/auth/token', json={'username': 'edge_user', 'password': 'pass'})
    token = auth_resp.get_json()['token']
    
    resp = api_client.get('/api/v1/customers?page=abc', headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 400
