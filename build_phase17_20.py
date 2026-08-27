import os

os.makedirs('app/employees', exist_ok=True)
os.makedirs('templates/employees', exist_ok=True)
os.makedirs('app/settings', exist_ok=True)
os.makedirs('templates/settings', exist_ok=True)
os.makedirs('app/rbac', exist_ok=True)
os.makedirs('templates/rbac', exist_ok=True)
os.makedirs('app/audit', exist_ok=True)
os.makedirs('templates/audit', exist_ok=True)

# ==========================================
# 1. UPDATE BASE STORAGE FOR AUDIT LOGGING
# ==========================================
storage_code = """import json
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
"""
with open('app/utils/storage.py', 'w', encoding='utf-8') as f:
    f.write(storage_code)


# ==========================================
# 2. EMPLOYEES BLUEPRINT
# ==========================================
with open('app/employees/__init__.py', 'w', encoding='utf-8') as f:
    f.write("from flask import Blueprint\nbp = Blueprint('employees', __name__)\nfrom app.employees import routes\n")

with open('app/employees/routes.py', 'w', encoding='utf-8') as f:
    f.write('''from flask import render_template, request, redirect, url_for, flash, current_app
from app.employees import bp
from app.auth.utils import login_required, role_required
from app.utils.storage import BaseStorage

def get_storage():
    return BaseStorage(current_app.config['DATA_DIR'], 'employees')

@bp.route('/employees')
@login_required
@role_required('Admin', 'Manager')
def list_employees():
    storage = get_storage()
    search_query = request.args.get('q', '').lower()
    all_employees = storage.get_all_records()
    if search_query:
        employees = [e for e in all_employees if search_query in e.get('name', '').lower() or search_query in e.get('department', '').lower()]
    else:
        employees = all_employees
    return render_template('employees/list.html', employees=employees, search_query=search_query)

@bp.route('/employees/create', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def create_employee():
    if request.method == 'POST':
        data = {
            'name': request.form.get('name'),
            'title': request.form.get('title'),
            'department': request.form.get('department'),
            'email': request.form.get('email'),
            'phone': request.form.get('phone'),
            'hire_date': request.form.get('hire_date'),
            'salary': request.form.get('salary', '0'),
            'performance_rating': request.form.get('performance_rating', 'N/A')
        }
        storage = get_storage()
        storage.create_record(data)
        flash('Employee created successfully.', 'success')
        return redirect(url_for('employees.list_employees'))
    return render_template('employees/create.html')
''')

with open('templates/employees/list.html', 'w', encoding='utf-8') as f:
    f.write('''{% extends "base/base.html" %}
{% block title %}Employees - SimpleCRM{% endblock %}
{% block content %}
<div class="card" style="display: flex; justify-content: space-between; align-items: center;">
    <h1>HR / Employees</h1>
    {% if session.get('user_role') == 'Admin' %}
    <a href="{{ url_for('employees.create_employee') }}" class="btn btn-primary">Add Employee</a>
    {% endif %}
</div>
<div class="card">
    <table style="width: 100%; border-collapse: collapse;">
        <thead>
            <tr style="border-bottom: 2px solid var(--border-color); text-align: left;">
                <th style="padding: 0.75rem;">Name</th><th style="padding: 0.75rem;">Title</th><th style="padding: 0.75rem;">Dept</th><th style="padding: 0.75rem;">Hire Date</th><th style="padding: 0.75rem;">Rating</th>
            </tr>
        </thead>
        <tbody>
            {% for e in employees %}
            <tr style="border-bottom: 1px solid var(--border-color);">
                <td style="padding: 0.75rem; font-weight: bold;">{{ e.name }}</td><td style="padding: 0.75rem;">{{ e.title }}</td><td style="padding: 0.75rem;">{{ e.department }}</td><td style="padding: 0.75rem;">{{ e.hire_date }}</td><td style="padding: 0.75rem;">{{ e.performance_rating }}</td>
            </tr>
            {% else %}
            <tr><td colspan="5" style="padding: 1rem; text-align: center;">No employees found.</td></tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}
''')

with open('templates/employees/create.html', 'w', encoding='utf-8') as f:
    f.write('''{% extends "base/base.html" %}
{% block content %}
<div class="card"><h1>Add Employee</h1><form method="POST">
    <div class="form-group"><label>Name</label><input type="text" name="name" required style="width:100%; padding:0.5rem;"></div>
    <div class="form-group"><label>Title</label><input type="text" name="title" style="width:100%; padding:0.5rem;"></div>
    <div class="form-group"><label>Department</label><input type="text" name="department" style="width:100%; padding:0.5rem;"></div>
    <div class="form-group"><label>Hire Date</label><input type="date" name="hire_date" style="width:100%; padding:0.5rem;"></div>
    <div class="form-group"><label>Salary ($)</label><input type="number" name="salary" style="width:100%; padding:0.5rem;"></div>
    <div class="form-group"><label>Rating</label><input type="text" name="performance_rating" style="width:100%; padding:0.5rem;"></div>
    <button type="submit" class="btn btn-primary" style="margin-top:1rem;">Save</button>
</form></div>
{% endblock %}
''')


# ==========================================
# 3. RBAC BLUEPRINT
# ==========================================
with open('app/rbac/__init__.py', 'w', encoding='utf-8') as f:
    f.write("from flask import Blueprint\nbp = Blueprint('rbac', __name__)\nfrom app.rbac import routes\n")

with open('app/rbac/routes.py', 'w', encoding='utf-8') as f:
    f.write('''from flask import render_template, request, redirect, url_for, flash, current_app
from app.rbac import bp
from app.auth.utils import login_required, role_required
from app.utils.storage import BaseStorage

@bp.route('/rbac')
@login_required
@role_required('Admin')
def list_roles():
    storage = BaseStorage(current_app.config['DATA_DIR'], 'users')
    users = storage.get_all_records()
    return render_template('rbac/list.html', users=users)

@bp.route('/rbac/update', methods=['POST'])
@login_required
@role_required('Admin')
def update_role():
    user_id = request.form.get('user_id')
    new_role = request.form.get('role')
    if user_id and new_role in ['Admin', 'Manager', 'User']:
        storage = BaseStorage(current_app.config['DATA_DIR'], 'users')
        storage.update_record(user_id, {'role': new_role})
        flash('User role updated.', 'success')
    return redirect(url_for('rbac.list_roles'))
''')

with open('templates/rbac/list.html', 'w', encoding='utf-8') as f:
    f.write('''{% extends "base/base.html" %}
{% block title %}RBAC - SimpleCRM{% endblock %}
{% block content %}
<div class="card"><h1>Role-Based Access Control</h1></div>
<div class="card">
    <table style="width: 100%; border-collapse: collapse;">
        <thead>
            <tr style="border-bottom: 2px solid var(--border-color); text-align: left;">
                <th style="padding: 0.75rem;">Username</th><th style="padding: 0.75rem;">Current Role</th><th style="padding: 0.75rem;">Change Role</th>
            </tr>
        </thead>
        <tbody>
            {% for u in users %}
            <tr style="border-bottom: 1px solid var(--border-color);">
                <td style="padding: 0.75rem;">{{ u.username }}</td>
                <td style="padding: 0.75rem; font-weight:bold;">{{ u.role }}</td>
                <td style="padding: 0.75rem;">
                    <form method="POST" action="{{ url_for('rbac.update_role') }}" style="display:flex; gap:0.5rem;">
                        <input type="hidden" name="user_id" value="{{ u.id }}">
                        <select name="role" style="padding:0.25rem;">
                            <option value="User" {% if u.role == 'User' %}selected{% endif %}>User</option>
                            <option value="Manager" {% if u.role == 'Manager' %}selected{% endif %}>Manager</option>
                            <option value="Admin" {% if u.role == 'Admin' %}selected{% endif %}>Admin</option>
                        </select>
                        <button class="btn btn-primary" style="padding:0.25rem 0.5rem;">Apply</button>
                    </form>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}
''')


# ==========================================
# 4. SETTINGS BLUEPRINT
# ==========================================
with open('app/settings/__init__.py', 'w', encoding='utf-8') as f:
    f.write("from flask import Blueprint\nbp = Blueprint('settings', __name__)\nfrom app.settings import routes\n")

with open('app/settings/routes.py', 'w', encoding='utf-8') as f:
    f.write('''from flask import render_template, request, redirect, url_for, flash, current_app
from app.settings import bp
from app.auth.utils import login_required, role_required
from app.utils.storage import BaseStorage

@bp.route('/settings', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def index():
    storage = BaseStorage(current_app.config['DATA_DIR'], 'settings')
    settings_records = storage.get_all_records()
    
    # Simple key-value structure
    settings = {}
    for r in settings_records:
        settings[r.get('key')] = r.get('value')
        
    if request.method == 'POST':
        keys = ['company_name', 'default_currency', 'timezone', 'theme']
        for k in keys:
            val = request.form.get(k)
            # Find existing
            existing = [r for r in settings_records if r.get('key') == k]
            if existing:
                storage.update_record(existing[0]['id'], {'value': val})
            else:
                storage.create_record({'key': k, 'value': val})
        flash('Settings updated successfully.', 'success')
        return redirect(url_for('settings.index'))
        
    return render_template('settings/index.html', settings=settings)
''')

with open('templates/settings/index.html', 'w', encoding='utf-8') as f:
    f.write('''{% extends "base/base.html" %}
{% block title %}System Settings - SimpleCRM{% endblock %}
{% block content %}
<div class="card"><h1>System Settings</h1></div>
<div class="card">
    <form method="POST">
        <div class="form-group" style="margin-bottom: 1rem;">
            <label>Company Name</label>
            <input type="text" name="company_name" value="{{ settings.get('company_name', 'SimpleCRM') }}" style="width:100%; padding:0.5rem;">
        </div>
        <div class="form-group" style="margin-bottom: 1rem;">
            <label>Default Currency Symbol</label>
            <input type="text" name="default_currency" value="{{ settings.get('default_currency', '$') }}" style="width:100%; padding:0.5rem;">
        </div>
        <div class="form-group" style="margin-bottom: 1rem;">
            <label>Timezone</label>
            <input type="text" name="timezone" value="{{ settings.get('timezone', 'UTC') }}" style="width:100%; padding:0.5rem;">
        </div>
        <div class="form-group" style="margin-bottom: 1rem;">
            <label>UI Theme</label>
            <select name="theme" style="width:100%; padding:0.5rem;">
                <option value="light" {% if settings.get('theme') == 'light' %}selected{% endif %}>Light Mode</option>
                <option value="dark" {% if settings.get('theme') == 'dark' %}selected{% endif %}>Dark Mode (CSS Optional)</option>
            </select>
        </div>
        <button type="submit" class="btn btn-primary">Save Settings</button>
    </form>
</div>
{% endblock %}
''')

# INJECT SETTINGS INTO CONTEXT PROCESSOR
with open('app/__init__.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add a context processor globally to inject company name
cp_code = """
    @app.context_processor
    def inject_settings():
        from app.utils.storage import BaseStorage
        storage = BaseStorage(app.config['DATA_DIR'], 'settings')
        settings = {r.get('key'): r.get('value') for r in storage.get_all_records()}
        return dict(global_settings=settings)
        
    return app
"""
if 'inject_settings' not in content:
    content = content.replace('return app', cp_code)
    
# Register blueprints
bp_registrations = """
    from app.employees import bp as employees_bp
    app.register_blueprint(employees_bp)
    from app.rbac import bp as rbac_bp
    app.register_blueprint(rbac_bp)
    from app.settings import bp as settings_bp
    app.register_blueprint(settings_bp)
    from app.audit import bp as audit_bp
    app.register_blueprint(audit_bp)

    @app.context_processor
"""
content = content.replace('@app.context_processor', bp_registrations)
with open('app/__init__.py', 'w', encoding='utf-8') as f:
    f.write(content)


# ==========================================
# 5. AUDIT BLUEPRINT
# ==========================================
with open('app/audit/__init__.py', 'w', encoding='utf-8') as f:
    f.write("from flask import Blueprint\nbp = Blueprint('audit', __name__)\nfrom app.audit import routes\n")

with open('app/audit/routes.py', 'w', encoding='utf-8') as f:
    f.write('''from flask import render_template, current_app
from app.audit import bp
from app.auth.utils import login_required, role_required
from app.utils.storage import BaseStorage

@bp.route('/audit')
@login_required
@role_required('Admin')
def index():
    storage = BaseStorage(current_app.config['DATA_DIR'], 'audit')
    # Get last 100 audit logs (reverse chronological)
    logs = storage.get_all_records()
    logs.reverse()
    return render_template('audit/index.html', logs=logs[:100])
''')

with open('templates/audit/index.html', 'w', encoding='utf-8') as f:
    f.write('''{% extends "base/base.html" %}
{% block title %}Audit Logs - SimpleCRM{% endblock %}
{% block content %}
<div class="card">
    <h1>System Audit Logs</h1>
    <p style="color:var(--text-muted);">Tracking global C-U-D operations. (Showing last 100)</p>
</div>
<div class="card" style="max-height: 600px; overflow-y: auto;">
    <table style="width: 100%; border-collapse: collapse; font-family: monospace; font-size: 0.9rem;">
        <thead>
            <tr style="border-bottom: 2px solid var(--border-color); text-align: left;">
                <th style="padding: 0.5rem;">Timestamp (UTC)</th>
                <th style="padding: 0.5rem;">User</th>
                <th style="padding: 0.5rem;">Action</th>
                <th style="padding: 0.5rem;">Module</th>
                <th style="padding: 0.5rem;">Record ID</th>
            </tr>
        </thead>
        <tbody>
            {% for log in logs %}
            <tr style="border-bottom: 1px solid var(--border-color); background: {% if loop.index is odd %}#f8fafc{% else %}#ffffff{% endif %};">
                <td style="padding: 0.5rem;">{{ log.timestamp }}</td>
                <td style="padding: 0.5rem;">{{ log.user }}</td>
                <td style="padding: 0.5rem; color: {% if log.action=='CREATE' %}var(--success-color){% elif log.action=='DELETE' %}var(--danger-color){% else %}#3b82f6{% endif %}; font-weight:bold;">{{ log.action }}</td>
                <td style="padding: 0.5rem;">{{ log.module }}</td>
                <td style="padding: 0.5rem; color: var(--text-muted);">{{ log.record_id }}</td>
            </tr>
            {% else %}
            <tr><td colspan="5" style="padding: 1rem; text-align: center;">No audit logs yet.</td></tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}
''')

# --- UPDATE BASE TEMPLATE NAV AND HEADER ---
with open('templates/base/base.html', 'r', encoding='utf-8') as f:
    base_html = f.read()

# Update header title to use dynamic setting
base_html = base_html.replace('SimpleCRM</a>', "{{ global_settings.get('company_name', 'SimpleCRM') }}</a>")

# Update nav (Admin only menu items)
if 'href="/settings"' not in base_html:
    admin_nav = '''
        <li style="margin-top:1rem; padding-left:1rem; font-size:0.75rem; text-transform:uppercase; color:#94a3b8; font-weight:bold;">Administration</li>
        <li><a href="{{ url_for('employees.list_employees') }}">HR / Employees</a></li>
        <li><a href="{{ url_for('rbac.list_roles') }}">User Roles</a></li>
        <li><a href="{{ url_for('audit.index') }}">Audit Logs</a></li>
        <li><a href="{{ url_for('settings.index') }}">Settings</a></li>
        <!-- Future links will go here -->'''
    base_html = base_html.replace('<!-- Future links will go here -->', admin_nav)
    with open('templates/base/base.html', 'w', encoding='utf-8') as f:
        f.write(base_html)
