import os
from werkzeug.security import generate_password_hash
from app import create_app
from app.utils.storage import BaseStorage

app = create_app()

with app.app_context():
    storage = BaseStorage(app.config['DATA_DIR'], 'users')
    existing = storage.search_records(username='admin')
    if not existing:
        storage.create_record({
            'username': 'admin',
            'password_hash': generate_password_hash('admin123'),
            'role': 'Admin',
            'status': 'Active',
            'email': 'admin@simplecrm.local'
        })
        print("Default admin user created. (admin / admin123)")
    else:
        print("Admin user already exists.")
