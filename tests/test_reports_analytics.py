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

def test_reports_index(auth_client):
    response = auth_client.get('/reports')
    assert response.status_code == 200
    assert b'Data Export & Reports' in response.data

def test_reports_export(auth_client, app):
    with app.app_context():
        storage = BaseStorage(app.config['DATA_DIR'], 'customers')
        storage.create_record({'first_name': 'Test', 'last_name': 'Customer'})
        
    response = auth_client.get('/reports/export/customers')
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'text/csv; charset=utf-8'
    assert b'Test' in response.data

def test_analytics_index(auth_client):
    response = auth_client.get('/analytics')
    assert response.status_code == 200
    assert b'Lead Conversion Rate' in response.data
    assert b'Opportunity Win Rate' in response.data
