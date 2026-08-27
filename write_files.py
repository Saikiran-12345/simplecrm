with open('app/utils/storage.py', 'w', encoding='utf-8') as f:
    f.write('''import json
import os
import uuid
import csv
from datetime import datetime, timezone
import threading

class BaseStorage:
    """
    Advanced Base class for local file storage supporting JSON and CSV.
    Thread-safe implementation for local Flask usage.
    """
    _locks = {}
    _locks_lock = threading.Lock()

    def __init__(self, data_dir, module_name, use_csv=False):
        self.data_dir = data_dir
        self.module_name = module_name
        self.use_csv = use_csv
        self.module_dir = os.path.join(self.data_dir, self.module_name)
        
        ext = 'csv' if self.use_csv else 'json'
        self.file_path = os.path.join(self.module_dir, f"{self.module_name}.{ext}")
        
        # Ensure a lock exists for this file
        with self._locks_lock:
            if self.file_path not in self._locks:
                self._locks[self.file_path] = threading.Lock()
        self.lock = self._locks[self.file_path]
        
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        with self.lock:
            if not os.path.exists(self.module_dir):
                os.makedirs(self.module_dir)
            if not os.path.exists(self.file_path):
                if self.use_csv:
                    with open(self.file_path, 'w', newline='', encoding='utf-8') as f:
                        pass
                else:
                    with open(self.file_path, 'w', encoding='utf-8') as f:
                        json.dump([], f)

    def _read_data(self):
        with self.lock:
            if not os.path.exists(self.file_path):
                return []
                
            if self.use_csv:
                try:
                    with open(self.file_path, 'r', newline='', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        if reader.fieldnames is None:
                            return []
                        return list(reader)
                except Exception:
                    return []
            else:
                try:
                    with open(self.file_path, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except (json.JSONDecodeError, FileNotFoundError):
                    return []

    def _write_data(self, data):
        with self.lock:
            if self.use_csv:
                if not data:
                    with open(self.file_path, 'w', newline='', encoding='utf-8') as f:
                        pass
                    return
                keys = list(data[0].keys())
                with open(self.file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=keys)
                    writer.writeheader()
                    writer.writerows(data)
            else:
                with open(self.file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4)

    def get_all_records(self):
        return self._read_data()

    def get_record(self, record_id):
        data = self._read_data()
        for item in data:
            if item.get('id') == record_id:
                return item
        return None

    def create_record(self, record_data):
        data = self._read_data()
        record_id = str(uuid.uuid4())
        record_data['id'] = record_id
        
        now = datetime.now(timezone.utc).isoformat()
        record_data['created_at'] = now
        record_data['updated_at'] = now
        
        data.append(record_data)
        self._write_data(data)
        return record_id

    def update_record(self, record_id, update_data):
        data = self._read_data()
        for i, item in enumerate(data):
            if item.get('id') == record_id:
                update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
                
                update_data['id'] = item['id']
                if 'created_at' in item:
                    update_data['created_at'] = item['created_at']
                
                data[i].update(update_data)
                self._write_data(data)
                return True
        return False

    def delete_record(self, record_id):
        data = self._read_data()
        new_data = [item for item in data if item.get('id') != record_id]
        if len(data) != len(new_data):
            self._write_data(new_data)
            return True
        return False

    def search_records(self, **kwargs):
        data = self._read_data()
        results = []
        for item in data:
            match = True
            for key, value in kwargs.items():
                if str(item.get(key, '')).lower() != str(value).lower():
                    match = False
                    break
            if match:
                results.append(item)
        return results

    def filter_records(self, filter_func):
        data = self._read_data()
        return [item for item in data if filter_func(item)]
''')

with open('tests/test_storage.py', 'w', encoding='utf-8') as f:
    f.write('''import os
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
''')
