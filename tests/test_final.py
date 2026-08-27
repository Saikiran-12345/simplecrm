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

def test_global_search(auth_client, app):
    with app.app_context():
        storage = BaseStorage(app.config['DATA_DIR'], 'customers')
        storage.create_record({'first_name': 'Searchable', 'last_name': 'Guy', 'company': 'FindMeInc'})
        
    response = auth_client.get('/search?q=findmeinc')
    assert response.status_code == 200
    assert b'Global Search Results' in response.data
    assert b'Searchable Guy' in response.data

def test_notifications(auth_client, app):
    with app.app_context():
        storage = BaseStorage(app.config['DATA_DIR'], 'notifications')
        storage.create_record({'user': 'admin', 'message': 'Test Alert', 'is_read': False})
        
    response = auth_client.get('/notifications')
    assert response.status_code == 200
    assert b'Test Alert' in response.data

def test_customer_validation(auth_client):
    # Customer without first_name should fail validation
    response = auth_client.post('/customers/create', data={
        'last_name': 'NoFirstName',
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Missing required fields' in response.data
