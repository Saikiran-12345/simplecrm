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

def test_invoices_list(auth_client):
    response = auth_client.get('/invoices')
    assert response.status_code == 200

def test_invoice_create(auth_client, app):
    with app.app_context():
        c_storage = BaseStorage(app.config['DATA_DIR'], 'customers')
        c_id = c_storage.create_record({'first_name': 'Bill', 'last_name': 'To'})
        p_storage = BaseStorage(app.config['DATA_DIR'], 'products')
        p_id = p_storage.create_record({'name': 'Service', 'price': '500'})
        
    response = auth_client.post('/invoices/create', data={
        'customer_id': c_id,
        'invoice_date': '2026-08-27',
        'due_date': '2026-09-27',
        'status': 'Draft',
        'product_id[]': [p_id],
        'quantity[]': ['1']
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Invoice created successfully' in response.data
    assert b'$500.00' in response.data

def test_payment_create(auth_client, app):
    with app.app_context():
        c_storage = BaseStorage(app.config['DATA_DIR'], 'customers')
        c_id = c_storage.create_record({'first_name': 'Pay', 'last_name': 'Guy'})
        i_storage = BaseStorage(app.config['DATA_DIR'], 'invoices')
        i_id = i_storage.create_record({'invoice_number': 'INV-TEST', 'status': 'Sent'})
        
    response = auth_client.post('/payments/create', data={
        'invoice_id': i_id,
        'customer_id': c_id,
        'amount': '250.00',
        'payment_date': '2026-08-27',
        'payment_method': 'Bank Transfer'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Payment recorded successfully' in response.data
    assert b'+$250.00' in response.data
    
    # Verify invoice status updated
    with app.app_context():
        inv = i_storage.get_record(i_id)
        assert inv['status'] == 'Paid'
