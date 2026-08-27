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

def test_notes_list(auth_client):
    response = auth_client.get('/notes')
    assert response.status_code == 200
    assert b'All Notes' in response.data

def test_note_create(auth_client, app):
    response = auth_client.post('/notes/create', data={
        'entity_type': 'Customer',
        'entity_id': '123',
        'content': 'This is a test note.',
        'return_url': '/notes'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Note added successfully' in response.data
    assert b'This is a test note.' in response.data

def test_dashboard_metrics(auth_client, app):
    # Just verify dashboard loads without error and contains the grid
    response = auth_client.get('/')
    assert response.status_code == 200
    assert b'Dashboard Overview' in response.data
    assert b'Customers' in response.data
    assert b'Opportunities' in response.data
    assert b'Invoices' in response.data
