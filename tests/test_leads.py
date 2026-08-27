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

def test_leads_list(auth_client):
    response = auth_client.get('/leads')
    assert response.status_code == 200
    assert b'Leads' in response.data

def test_lead_create(auth_client):
    response = auth_client.post('/leads/create', data={
        'name': 'Potential Client',
        'company': 'Big Bucks LLC',
        'status': 'New',
        'priority': 'High'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Lead created successfully.' in response.data
    assert b'Big Bucks LLC' in response.data

def test_lead_edit(auth_client, app):
    with app.app_context():
        storage = BaseStorage(app.config['DATA_DIR'], 'leads')
        l_id = storage.create_record({'name': 'Old Lead', 'status': 'New'})
        
    response = auth_client.post(f'/leads/{l_id}/edit', data={
        'name': 'Updated Lead',
        'status': 'Contacted'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Lead updated successfully.' in response.data
    assert b'Contacted' in response.data

def test_lead_convert(auth_client, app):
    with app.app_context():
        storage = BaseStorage(app.config['DATA_DIR'], 'leads')
        l_id = storage.create_record({
            'name': 'John Smith',
            'company': 'Smith Co',
            'status': 'Qualified',
            'email': 'john@smith.com'
        })
        
    response = auth_client.post(f'/leads/{l_id}/convert', follow_redirects=True)
    assert response.status_code == 200
    assert b'Lead successfully converted to Customer!' in response.data
    
    # Check that lead is converted
    with app.app_context():
        l = storage.get_record(l_id)
        assert l['status'] == 'Converted'
        assert 'converted_to_customer_id' in l
        
        # Check customer was actually created
        c_storage = BaseStorage(app.config['DATA_DIR'], 'customers')
        c = c_storage.get_record(l['converted_to_customer_id'])
        assert c['first_name'] == 'John'
        assert c['last_name'] == 'Smith'
        assert c['company'] == 'Smith Co'

def test_lead_delete(auth_client, app):
    with app.app_context():
        storage = BaseStorage(app.config['DATA_DIR'], 'leads')
        l_id = storage.create_record({'name': 'To Delete'})
        
    response = auth_client.post(f'/leads/{l_id}/delete', follow_redirects=True)
    assert response.status_code == 200
    assert b'Lead deleted successfully.' in response.data
