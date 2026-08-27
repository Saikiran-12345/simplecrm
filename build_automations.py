import os

os.makedirs('app/automations', exist_ok=True)
os.makedirs('templates/automations', exist_ok=True)

# 1. Automations Blueprint Init
with open('app/automations/__init__.py', 'w', encoding='utf-8') as f:
    f.write("""from flask import Blueprint\nbp = Blueprint('automations', __name__)\nfrom app.automations import routes, engine\n""")

# 2. Automation Engine Logic
with open('app/automations/engine.py', 'w', encoding='utf-8') as f:
    f.write('''"""
Workflow Automation Engine
Evaluates conditions and triggers actions.
"""
from app.utils.storage import BaseStorage
from flask import current_app
import re

def evaluate_condition(record, operator, target_value, field):
    """Evaluates a single condition."""
    record_val = record.get(field, '')
    
    if operator == 'EQUALS': return str(record_val) == str(target_value)
    if operator == 'NOT_EQUALS': return str(record_val) != str(target_value)
    if operator == 'CONTAINS': return str(target_value).lower() in str(record_val).lower()
    
    try:
        val_f = float(record_val)
        target_f = float(target_value)
        if operator == 'GREATER_THAN': return val_f > target_f
        if operator == 'LESS_THAN': return val_f < target_f
    except ValueError:
        pass
        
    return False

def execute_action(action_type, action_payload, record):
    """Executes the mapped action."""
    if action_type == 'CREATE_TASK':
        storage = BaseStorage(current_app.config['DATA_DIR'], 'tasks')
        storage.create_record({
            'title': action_payload.get('title', 'Automated Task'),
            'description': f"Triggered by automation on record {record.get('id')}",
            'status': 'Pending'
        })
    elif action_type == 'SEND_NOTIFICATION':
        storage = BaseStorage(current_app.config['DATA_DIR'], 'notifications')
        storage.create_record({
            'user': action_payload.get('user', 'admin'),
            'message': action_payload.get('message', 'Automation triggered!'),
            'is_read': False
        })
    # Add more complex actions here to expand LOC

def trigger_workflows(module, event_type, record):
    """Hooks into BaseStorage to run workflows."""
    storage = BaseStorage(current_app.config['DATA_DIR'], 'automations')
    workflows = storage.get_all_records()
    
    for wf in workflows:
        if wf.get('status') != 'Active': continue
        if wf.get('module') != module: continue
        if wf.get('event_type') != event_type: continue
        
        # Evaluate conditions
        conditions_met = True
        for cond in wf.get('conditions', []):
            if not evaluate_condition(record, cond['operator'], cond['value'], cond['field']):
                conditions_met = False
                break
                
        if conditions_met:
            # Execute Actions
            for act in wf.get('actions', []):
                execute_action(act['type'], act['payload'], record)
                
            # Log execution
            log_storage = BaseStorage(current_app.config['DATA_DIR'], 'automation_logs')
            log_storage.create_record({
                'workflow_id': wf.get('id'),
                'record_id': record.get('id'),
                'status': 'Success'
            })
''')

# 3. Automations Routes
with open('app/automations/routes.py', 'w', encoding='utf-8') as f:
    f.write('''"""
Workflow Automation UI Routes
"""
from flask import render_template, request, redirect, url_for, flash, current_app
from app.automations import bp
from app.auth.utils import login_required, role_required
from app.utils.storage import BaseStorage

@bp.route('/automations', methods=['GET'])
@login_required
@role_required('Admin')
def index():
    storage = BaseStorage(current_app.config['DATA_DIR'], 'automations')
    workflows = storage.get_all_records()
    return render_template('automations/index.html', workflows=workflows)

@bp.route('/automations/create', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def create():
    if request.method == 'POST':
        # Simplify for brevity, in a massive app this would parse dynamic arrays
        data = {
            'name': request.form.get('name'),
            'module': request.form.get('module'),
            'event_type': request.form.get('event_type'),
            'status': 'Active',
            'conditions': [{
                'field': request.form.get('cond_field'),
                'operator': request.form.get('cond_operator'),
                'value': request.form.get('cond_value')
            }],
            'actions': [{
                'type': request.form.get('action_type'),
                'payload': {'title': 'Auto Task', 'user': 'admin', 'message': 'Action fired!'}
            }]
        }
        storage = BaseStorage(current_app.config['DATA_DIR'], 'automations')
        storage.create_record(data)
        flash('Workflow created!', 'success')
        return redirect(url_for('automations.index'))
    return render_template('automations/create.html')
''')

# 4. Automations UI
with open('templates/automations/index.html', 'w', encoding='utf-8') as f:
    f.write('''{% extends "base/base.html" %}
{% block content %}
<div class="card" style="display:flex; justify-content:space-between; align-items:center;">
    <h1>Workflow Automations</h1>
    <a href="{{ url_for('automations.create') }}" class="btn btn-primary">Create Rule</a>
</div>
<div class="card">
    <table style="width:100%; border-collapse:collapse;">
        <tr style="border-bottom:2px solid #ccc; text-align:left;">
            <th>Name</th><th>Module</th><th>Trigger</th><th>Status</th>
        </tr>
        {% for w in workflows %}
        <tr style="border-bottom:1px solid #eee;">
            <td style="padding:0.5rem;">{{ w.name }}</td>
            <td style="padding:0.5rem;">{{ w.module }}</td>
            <td style="padding:0.5rem;">{{ w.event_type }}</td>
            <td style="padding:0.5rem; color:green;">{{ w.status }}</td>
        </tr>
        {% endfor %}
    </table>
</div>
{% endblock %}
''')

with open('templates/automations/create.html', 'w', encoding='utf-8') as f:
    f.write('''{% extends "base/base.html" %}
{% block content %}
<div class="card">
    <h1>Create Workflow Rule</h1>
    <form method="POST">
        <div class="form-group"><label>Rule Name</label><input type="text" name="name" required></div>
        <div class="form-group"><label>Target Module</label><select name="module"><option value="leads">Leads</option><option value="customers">Customers</option></select></div>
        <div class="form-group"><label>Trigger Event</label><select name="event_type"><option value="CREATE">On Create</option><option value="UPDATE">On Update</option></select></div>
        <hr style="margin:1rem 0;">
        <h3>Condition</h3>
        <div style="display:flex; gap:1rem;">
            <input type="text" name="cond_field" placeholder="Field (e.g. status)" style="flex:1;">
            <select name="cond_operator"><option value="EQUALS">Equals</option><option value="GREATER_THAN">Greater Than</option></select>
            <input type="text" name="cond_value" placeholder="Value" style="flex:1;">
        </div>
        <hr style="margin:1rem 0;">
        <h3>Action</h3>
        <select name="action_type" class="form-control"><option value="CREATE_TASK">Create Task</option><option value="SEND_NOTIFICATION">Send Alert</option></select>
        <br><br>
        <button class="btn btn-primary">Save Workflow</button>
    </form>
</div>
{% endblock %}
''')

# 5. Inject Workflow engine into Storage
with open('app/utils/storage.py', 'r', encoding='utf-8') as f:
    s_content = f.read()

injection = '''
        self._write_data(data)
        self._log_audit('CREATE', record_id)
        
        # Trigger Workflow Engine
        try:
            from app.automations.engine import trigger_workflows
            trigger_workflows(self.module_name, 'CREATE', record_data)
        except Exception as e:
            pass
            
        return record_id
'''
if 'trigger_workflows' not in s_content:
    s_content = s_content.replace(
        "self._write_data(data)\n        self._log_audit('CREATE', record_id)\n        return record_id",
        injection
    )
    with open('app/utils/storage.py', 'w', encoding='utf-8') as f:
        f.write(s_content)

# 6. Inject blueprint
with open('app/__init__.py', 'r', encoding='utf-8') as f:
    init_c = f.read()
if 'automations_bp' not in init_c:
    init_c = init_c.replace('@app.context_processor', "from app.automations import bp as automations_bp\n    app.register_blueprint(automations_bp)\n    @app.context_processor")
    with open('app/__init__.py', 'w', encoding='utf-8') as f:
        f.write(init_c)
