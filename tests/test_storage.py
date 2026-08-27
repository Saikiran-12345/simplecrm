import os
import pytest
from app.utils.storage import BaseStorage
from datetime import datetime, timezone

@pytest.fixture
def storage(app):
    return BaseStorage(data_dir=app.config['DATA_DIR'], module_name='test_module_json', use_csv=False)

@pytest.fixture
def csv_storage(app):
    return BaseStorage(data_dir=app.config['DATA_DIR'], module_name='test_module_csv', use_csv=True)

def test_json_crud(storage):
    r_id = storage.create_record({'name': 'JSON Test'})
    assert r_id is not None
    r = storage.get_record(r_id)
    assert r['name'] == 'JSON Test'
    storage.update_record(r_id, {'name': 'Updated JSON'})
    r2 = storage.get_record(r_id)
    assert r2['name'] == 'Updated JSON'
    storage.delete_record(r_id)
    assert storage.get_record(r_id) is None

def test_csv_crud(csv_storage):
    r_id = csv_storage.create_record({'name': 'CSV Test', 'value': '123'})
    assert r_id is not None
    r = csv_storage.get_record(r_id)
    assert r['name'] == 'CSV Test'
    assert r['value'] == '123'
    csv_storage.update_record(r_id, {'name': 'CSV Updated', 'value': '456'})
    r2 = csv_storage.get_record(r_id)
    assert r2['name'] == 'CSV Updated'
    csv_storage.delete_record(r_id)
    assert csv_storage.get_record(r_id) is None

def test_filter_records(storage):
    storage.create_record({'amount': 50})
    storage.create_record({'amount': 150})
    storage.create_record({'amount': 200})
    
    results = storage.filter_records(lambda x: int(x.get('amount', 0)) > 100)
    assert len(results) == 2
