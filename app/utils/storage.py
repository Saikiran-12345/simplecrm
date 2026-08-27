import json
import os
import uuid
import threading
from datetime import datetime
from flask import has_request_context, session

class BaseStorage:
    _locks = {}

    def __init__(self, data_dir, module_name):
        self.data_dir = data_dir
        self.module_name = module_name
        self.file_path = os.path.join(data_dir, module_name, f"{module_name}.json")
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        
        if self.file_path not in self._locks:
            self._locks[self.file_path] = threading.Lock()
            
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump([], f)

    def _log_audit(self, action, record_id):
        if self.module_name == 'audit': return # Prevent infinite loop
        user = 'System'
        if has_request_context():
            user = session.get('username', 'Unknown')
            
        audit_file = os.path.join(self.data_dir, 'audit', 'audit.json')
        os.makedirs(os.path.dirname(audit_file), exist_ok=True)
        
        if audit_file not in self._locks:
            self._locks[audit_file] = threading.Lock()
            
        if not os.path.exists(audit_file):
            with open(audit_file, 'w', encoding='utf-8') as f: json.dump([], f)
            
        with self._locks[audit_file]:
            try:
                with open(audit_file, 'r', encoding='utf-8') as f: data = json.load(f)
            except:
                data = []
            
            data.append({
                'id': str(uuid.uuid4()),
                'timestamp': datetime.utcnow().isoformat() + "Z",
                'user': user,
                'action': action,
                'module': self.module_name,
                'record_id': record_id
            })
            
            with open(audit_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)

    def _read_data(self):
        with self._locks[self.file_path]:
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return []

    def _write_data(self, data):
        with self._locks[self.file_path]:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)


    def search_records(self, **kwargs):
        data = self._read_data()
        results = []
        for record in data:
            match = True
            for k, v in kwargs.items():
                if record.get(k) != v:
                    match = False
                    break
            if match:
                results.append(record)
        return results

    def get_all_records(self):

        return self._read_data()

    def get_record(self, record_id):
        data = self._read_data()
        for record in data:
            if record.get('id') == record_id:
                return record
        return None

    def create_record(self, record_data):
        data = self._read_data()
        record_id = str(uuid.uuid4())
        record_data['id'] = record_id
        record_data['created_at'] = datetime.utcnow().isoformat() + "Z"
        data.append(record_data)
        
        self._write_data(data)
        self._log_audit('CREATE', record_id)
        
        # Trigger Workflow Engine
        try:
            from app.automations.engine import trigger_workflows
            trigger_workflows(self.module_name, 'CREATE', record_data)
        except Exception as e:
            pass
            
        return record_id


    def update_record(self, record_id, updated_data):
        data = self._read_data()
        for i, record in enumerate(data):
            if record.get('id') == record_id:
                for key in ['id', 'created_at']:
                    if key in updated_data:
                        del updated_data[key]
                data[i].update(updated_data)
                self._write_data(data)
                self._log_audit('UPDATE', record_id)
                return True
        return False

    def delete_record(self, record_id):
        data = self._read_data()
        new_data = [r for r in data if r.get('id') != record_id]
        if len(new_data) < len(data):
            self._write_data(new_data)
            self._log_audit('DELETE', record_id)
            return True
        return False
