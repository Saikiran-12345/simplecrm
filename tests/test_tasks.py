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

def test_tasks_list(auth_client):
    response = auth_client.get('/tasks')
    assert response.status_code == 200

def test_task_create(auth_client):
    response = auth_client.post('/tasks/create', data={
        'description': 'Call John',
        'status': 'Pending'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Task created successfully' in response.data
