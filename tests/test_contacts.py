import pytest
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

def test_contacts_list(auth_client):
    response = auth_client.get('/contacts')
    assert response.status_code == 200
    assert b'Contacts' in response.data

def test_contact_create(auth_client, app):
    # Setup a customer first
    with app.app_context():
        c_storage = BaseStorage(app.config['DATA_DIR'], 'customers')
        cust_id = c_storage.create_record({'first_name': 'Cust', 'last_name': 'One', 'company': 'TestCorp'})
        
    response = auth_client.post('/contacts/create', data={
        'first_name': 'John',
        'last_name': 'Doe',
        'title': 'Manager',
        'customer_id': cust_id,
        'email': 'john@testcorp.com'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Contact created successfully.' in response.data
    assert b'John Doe' in response.data

def test_contact_edit(auth_client, app):
    with app.app_context():
        storage = BaseStorage(app.config['DATA_DIR'], 'contacts')
        c_id = storage.create_record({'first_name': 'Jane', 'last_name': 'Doe'})
        
    response = auth_client.post(f'/contacts/{c_id}/edit', data={
        'first_name': 'Janet',
        'last_name': 'Doe',
        'email': 'janet@example.com'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Contact updated successfully.' in response.data
    assert b'Janet Doe' in response.data

def test_contact_delete(auth_client, app):
    with app.app_context():
        storage = BaseStorage(app.config['DATA_DIR'], 'contacts')
        c_id = storage.create_record({'first_name': 'ToDelete', 'last_name': 'Soon'})
        
    response = auth_client.post(f'/contacts/{c_id}/delete', follow_redirects=True)
    assert response.status_code == 200
    assert b'Contact deleted successfully.' in response.data
