import os

os.makedirs('app/custom_fields', exist_ok=True)
os.makedirs('templates/custom_fields', exist_ok=True)

# 1. Custom Fields Blueprint
with open('app/custom_fields/__init__.py', 'w', encoding='utf-8') as f:
    f.write("from flask import Blueprint\nbp = Blueprint('custom_fields', __name__)\nfrom app.custom_fields import routes\n")

# 2. Custom Fields Routes
with open('app/custom_fields/routes.py', 'w', encoding='utf-8') as f:
    f.write('''"""
Dynamic Custom Fields Module
Allows Admins to define new fields for any module without altering database schema.
"""
from flask import render_template, request, redirect, url_for, flash, current_app
from app.custom_fields import bp
from app.auth.utils import login_required, role_required
from app.utils.storage import BaseStorage

@bp.route('/custom-fields', methods=['GET'])
@login_required
@role_required('Admin')
def index():
    storage = BaseStorage(current_app.config['DATA_DIR'], 'custom_fields')
    fields = storage.get_all_records()
    return render_template('custom_fields/index.html', fields=fields)

@bp.route('/custom-fields/create', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def create():
    if request.method == 'POST':
        data = {
            'module': request.form.get('module'),
            'field_name': request.form.get('field_name').replace(' ', '_').lower(),
            'field_label': request.form.get('field_label'),
            'field_type': request.form.get('field_type'),
            'is_required': request.form.get('is_required') == 'on'
        }
        storage = BaseStorage(current_app.config['DATA_DIR'], 'custom_fields')
        storage.create_record(data)
        flash('Custom Field created!', 'success')
        return redirect(url_for('custom_fields.index'))
    return render_template('custom_fields/create.html')
''')

# 3. Custom Fields UI
with open('templates/custom_fields/index.html', 'w', encoding='utf-8') as f:
    f.write('''{% extends "base/base.html" %}
{% block content %}
<div class="card" style="display:flex; justify-content:space-between; align-items:center;">
    <h1>Custom Fields Definition</h1>
    <a href="{{ url_for('custom_fields.create') }}" class="btn btn-primary">Add Field</a>
</div>
<div class="card">
    <table style="width:100%; border-collapse:collapse;">
        <tr style="border-bottom:2px solid #ccc; text-align:left;">
            <th>Module</th><th>Label</th><th>Internal Name</th><th>Type</th><th>Required</th>
        </tr>
        {% for f in fields %}
        <tr style="border-bottom:1px solid #eee;">
            <td style="padding:0.5rem;">{{ f.module }}</td>
            <td style="padding:0.5rem;">{{ f.field_label }}</td>
            <td style="padding:0.5rem;"><code>{{ f.field_name }}</code></td>
            <td style="padding:0.5rem;">{{ f.field_type }}</td>
            <td style="padding:0.5rem;">{{ 'Yes' if f.is_required else 'No' }}</td>
        </tr>
        {% endfor %}
    </table>
</div>
{% endblock %}
''')

with open('templates/custom_fields/create.html', 'w', encoding='utf-8') as f:
    f.write('''{% extends "base/base.html" %}
{% block content %}
<div class="card">
    <h1>Define New Custom Field</h1>
    <form method="POST">
        <div class="form-group"><label>Target Module</label><select name="module"><option value="customers">Customers</option><option value="leads">Leads</option><option value="products">Products</option></select></div>
        <div class="form-group"><label>Field Label</label><input type="text" name="field_label" required placeholder="e.g. Tax ID"></div>
        <div class="form-group"><label>Internal Name (no spaces)</label><input type="text" name="field_name" required placeholder="e.g. tax_id"></div>
        <div class="form-group"><label>Field Type</label><select name="field_type"><option value="text">Text String</option><option value="number">Number</option><option value="date">Date</option></select></div>
        <div class="form-group"><label><input type="checkbox" name="is_required"> Required Field</label></div>
        <button class="btn btn-primary">Save Custom Field</button>
    </form>
</div>
{% endblock %}
''')

# 4. Context Processor to inject Custom Fields dynamically into Templates
with open('app/__init__.py', 'r', encoding='utf-8') as f:
    init_c = f.read()

injection = '''
        custom_fields = {}
        try:
            cf_storage = BaseStorage(app.config['DATA_DIR'], 'custom_fields')
            cfs = cf_storage.get_all_records()
            for f in cfs:
                mod = f.get('module')
                if mod not in custom_fields: custom_fields[mod] = []
                custom_fields[mod].append(f)
        except Exception:
            pass
            
        return dict(global_settings=settings, unread_notifications=unread_count, custom_fields=custom_fields)
'''
if 'custom_fields=custom_fields' not in init_c:
    init_c = init_c.replace('return dict(global_settings=settings, unread_notifications=unread_count)', injection)
    init_c = init_c.replace('@app.context_processor', "from app.custom_fields import bp as custom_fields_bp\n    app.register_blueprint(custom_fields_bp)\n    @app.context_processor")
    with open('app/__init__.py', 'w', encoding='utf-8') as f:
        f.write(init_c)
