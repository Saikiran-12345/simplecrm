import pytest
from flask import session
from werkzeug.security import generate_password_hash
from app.utils.storage import BaseStorage

@pytest.fixture
def auth_client(client, app):
    # Create an admin user for testing
    with app.app_context():
        storage = BaseStorage(app.config['DATA_DIR'], 'users')
        storage.create_record({
            'username': 'testadmin',
            'password_hash': generate_password_hash('testpass'),
            'role': 'Admin',
            'status': 'Active'
        })
    return client

def test_login_page_renders(client):
    response = client.get('/auth/login')
    assert response.status_code == 200
    assert b'SimpleCRM Login' in response.data

def test_login_success(auth_client):
    response = auth_client.post('/auth/login', data={
        'username': 'testadmin',
        'password': 'testpass'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Successfully logged in.' in response.data
    assert b'Dashboard' in response.data

def test_login_failure(auth_client):
    response = auth_client.post('/auth/login', data={
        'username': 'testadmin',
        'password': 'wrongpassword'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Invalid username or password.' in response.data

def test_protected_route(client):
    # Trying to access dashboard without login
    response = client.get('/', follow_redirects=True)
    assert response.status_code == 200
    assert b'Please log in to access this page.' in response.data
    assert b'SimpleCRM Login' in response.data

def test_logout(auth_client):
    # Log in first
    auth_client.post('/auth/login', data={'username': 'testadmin', 'password': 'testpass'})
    # Log out
    response = auth_client.get('/auth/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'You have been logged out.' in response.data
