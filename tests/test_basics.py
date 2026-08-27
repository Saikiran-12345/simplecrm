def test_app_exists(app):
    assert app is not None

def test_app_is_testing(app):
    assert app.config['TESTING']

def test_index_page(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'Welcome to SimpleCRM' in response.data

def test_404_error(client):
    response = client.get('/nonexistent-page')
    assert response.status_code == 404
    assert b'Page Not Found' in response.data
