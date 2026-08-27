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

def test_products_list(auth_client):
    response = auth_client.get('/products')
    assert response.status_code == 200

def test_product_create(auth_client):
    response = auth_client.post('/products/create', data={
        'name': 'Test Widget',
        'category': 'Widgets',
        'price': '10.50',
        'quantity': '100'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Product created successfully' in response.data

def test_sales_create(auth_client, app):
    # Setup customer and product
    with app.app_context():
        c_storage = BaseStorage(app.config['DATA_DIR'], 'customers')
        c_id = c_storage.create_record({'first_name': 'Buy', 'last_name': 'Guy'})
        
        p_storage = BaseStorage(app.config['DATA_DIR'], 'products')
        p_id = p_storage.create_record({'name': 'Expensive Gadget', 'price': '100.0', 'quantity': '10'})
        
    response = auth_client.post('/sales/create', data={
        'customer_id': c_id,
        'sales_date': '2026-08-27',
        'product_id[]': [p_id],
        'quantity[]': ['2'],
        'discount': '10',
        'tax': '5'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Sale created successfully.' in response.data
    assert b'$199.50' in response.data # (100*2 = 200) - 10 discount = 190 + 5% tax (9.5) = 199.50
    
    # Check inventory deduction
    with app.app_context():
        p = p_storage.get_record(p_id)
        assert float(p['quantity']) == 8.0
