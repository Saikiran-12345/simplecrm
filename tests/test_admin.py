import pytest
from app.utils.storage import BaseStorage
import os

@pytest.fixture
def auth_client(client, app):
    with app.app_context():
        storage = BaseStorage(app.config['DATA_DIR'], 'users')
        user_id = storage.create_record({
            'username': 'admin',
            'role': 'Admin',
            'status': 'Active'
        })
    with client.session_transaction() as sess:
        sess['user_id'] = user_id
        sess['user_role'] = 'Admin'
        sess['username'] = 'admin'
    return client

def test_employees_list(auth_client):
    response = auth_client.get('/employees')
    assert response.status_code == 200

def test_employee_create(auth_client):
    response = auth_client.post('/employees/create', data={
        'name': 'John Employee',
        'title': 'Sales Rep',
        'department': 'Sales'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Employee created successfully' in response.data

def test_rbac_list(auth_client):
    response = auth_client.get('/rbac')
    assert response.status_code == 200
    assert b'Role-Based Access Control' in response.data

def test_settings_update(auth_client, app):
    response = auth_client.post('/settings', data={
        'company_name': 'MyMegaCorp',
        'default_currency': 'EUR'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Settings updated successfully' in response.data
    
    # Test context processor rendered it in the header
    response = auth_client.get('/')
    assert b'MyMegaCorp' in response.data

def test_audit_logs(auth_client, app):
    # Action should have been logged globally by employee creation
    response = auth_client.get('/audit')
    assert response.status_code == 200
    assert b'CREATE' in response.data
    assert b'employees' in response.data

