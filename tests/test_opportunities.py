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

def test_opportunities_list(auth_client):
    response = auth_client.get('/opportunities')
    assert response.status_code == 200
    assert b'Opportunities' in response.data

def test_opportunity_create(auth_client):
    response = auth_client.post('/opportunities/create', data={
        'title': 'Big Deal',
        'value': '10000',
        'probability': '50',
        'stage': 'Qualification'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Opportunity created successfully.' in response.data
    assert b'Big Deal' in response.data

def test_opportunity_edit(auth_client, app):
    with app.app_context():
        storage = BaseStorage(app.config['DATA_DIR'], 'opportunities')
        o_id = storage.create_record({'title': 'Old Title', 'stage': 'New'})
        
    response = auth_client.post(f'/opportunities/{o_id}/edit', data={
        'title': 'New Title',
        'value': '5000',
        'probability': '90',
        'stage': 'Proposal'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Opportunity updated successfully.' in response.data
    assert b'New Title' in response.data
    assert b'$5000' in response.data

def test_opportunity_delete(auth_client, app):
    with app.app_context():
        storage = BaseStorage(app.config['DATA_DIR'], 'opportunities')
        o_id = storage.create_record({'title': 'To Delete'})
        
    response = auth_client.post(f'/opportunities/{o_id}/delete', follow_redirects=True)
    assert response.status_code == 200
    assert b'Opportunity deleted successfully.' in response.data
