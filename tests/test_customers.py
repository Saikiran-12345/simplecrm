import pytest
from flask import session
from app.utils.storage import BaseStorage

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

def test_customers_list(auth_client):
    response = auth_client.get('/customers')
    assert response.status_code == 200
    assert b'Customers' in response.data
    assert b'Add Customer' in response.data

def test_customer_create_and_view(auth_client):
    response = auth_client.post('/customers/create', data={
        'first_name': 'Test',
        'last_name': 'Customer',
        'company': 'ACME Corp',
        'email': 'test@acme.com',
        'status': 'Active'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Customer created successfully.' in response.data
    assert b'ACME Corp' in response.data

def test_customer_edit(auth_client, app):
    # First create via storage
    with app.app_context():
        storage = BaseStorage(app.config['DATA_DIR'], 'customers')
        c_id = storage.create_record({'first_name': 'Old', 'last_name': 'Name'})
        
    response = auth_client.post(f'/customers/{c_id}/edit', data={
        'first_name': 'New',
        'last_name': 'Name',
        'company': 'New Corp'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Customer updated successfully.' in response.data
    assert b'New Corp' in response.data

def test_customer_delete(auth_client, app):
    with app.app_context():
        storage = BaseStorage(app.config['DATA_DIR'], 'customers')
        c_id = storage.create_record({'first_name': 'To', 'last_name': 'Delete'})
        
    response = auth_client.post(f'/customers/{c_id}/delete', follow_redirects=True)
    assert response.status_code == 200
    assert b'Customer deleted successfully.' in response.data
    
    with app.app_context():
        assert storage.get_record(c_id) is None
