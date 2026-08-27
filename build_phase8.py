import os

# Create directories
os.makedirs('app/tasks', exist_ok=True)
os.makedirs('templates/tasks', exist_ok=True)
os.makedirs('app/followups', exist_ok=True)
os.makedirs('templates/followups', exist_ok=True)

# --- TASKS BLUEPRINT ---
with open('app/tasks/__init__.py', 'w', encoding='utf-8') as f:
    f.write('''from flask import Blueprint
bp = Blueprint('tasks', __name__)
from app.tasks import routes
''')

with open('app/tasks/routes.py', 'w', encoding='utf-8') as f:
    f.write('''from flask import render_template, request, redirect, url_for, flash, current_app
from app.tasks import bp
from app.auth.utils import login_required
from app.utils.storage import BaseStorage
from datetime import datetime

def get_storage(name):
    return BaseStorage(current_app.config['DATA_DIR'], name)

@bp.route('/tasks')
@login_required
def list_tasks():
    storage = get_storage('tasks')
    search_query = request.args.get('q', '').lower()
    all_tasks = storage.get_all_records()
    
    # Overdue detection
    today = datetime.today().strftime('%Y-%m-%d')
    for t in all_tasks:
        if t.get('status') not in ['Completed', 'Cancelled'] and t.get('due_date') and t.get('due_date') < today:
            t['is_overdue'] = True
        else:
            t['is_overdue'] = False
            
    if search_query:
        tasks = [t for t in all_tasks if search_query in t.get('description', '').lower()]
    else:
        tasks = all_tasks
        
    return render_template('tasks/list.html', tasks=tasks, search_query=search_query)

@bp.route('/tasks/create', methods=['GET', 'POST'])
@login_required
def create_task():
    if request.method == 'POST':
        data = {
            'description': request.form.get('description'),
            'due_date': request.form.get('due_date'),
            'priority': request.form.get('priority', 'Medium'),
            'status': request.form.get('status', 'Pending'),
            'assigned_employee': request.form.get('assigned_employee', ''),
            'customer_id': request.form.get('customer_id', ''),
            'lead_id': request.form.get('lead_id', '')
        }
        storage = get_storage('tasks')
        storage.create_record(data)
        flash('Task created successfully.', 'success')
        return redirect(url_for('tasks.list_tasks'))
        
    customers = get_storage('customers').get_all_records()
    leads = get_storage('leads').get_all_records()
    return render_template('tasks/create.html', customers=customers, leads=leads)

@bp.route('/tasks/<record_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_task(record_id):
    storage = get_storage('tasks')
    task = storage.get_record(record_id)
    if not task:
        flash('Task not found.', 'danger')
        return redirect(url_for('tasks.list_tasks'))
        
    if request.method == 'POST':
        data = {
            'description': request.form.get('description'),
            'due_date': request.form.get('due_date'),
            'priority': request.form.get('priority'),
            'status': request.form.get('status'),
            'assigned_employee': request.form.get('assigned_employee'),
            'customer_id': request.form.get('customer_id'),
            'lead_id': request.form.get('lead_id')
        }
        storage.update_record(record_id, data)
        flash('Task updated successfully.', 'success')
        return redirect(url_for('tasks.list_tasks'))
        
    customers = get_storage('customers').get_all_records()
    leads = get_storage('leads').get_all_records()
    return render_template('tasks/edit.html', task=task, customers=customers, leads=leads)

@bp.route('/tasks/<record_id>/delete', methods=['POST'])
@login_required
def delete_task(record_id):
    storage = get_storage('tasks')
    if storage.delete_record(record_id):
        flash('Task deleted successfully.', 'success')
    else:
        flash('Task not found.', 'danger')
    return redirect(url_for('tasks.list_tasks'))
''')

# --- FOLLOWUPS BLUEPRINT ---
with open('app/followups/__init__.py', 'w', encoding='utf-8') as f:
    f.write('''from flask import Blueprint
bp = Blueprint('followups', __name__)
from app.followups import routes
''')

with open('app/followups/routes.py', 'w', encoding='utf-8') as f:
    f.write('''from flask import render_template, request, redirect, url_for, flash, current_app
from app.followups import bp
from app.auth.utils import login_required
from app.utils.storage import BaseStorage
from datetime import datetime

def get_storage(name):
    return BaseStorage(current_app.config['DATA_DIR'], name)

@bp.route('/followups')
@login_required
def list_followups():
    storage = get_storage('followups')
    search_query = request.args.get('q', '').lower()
    all_followups = storage.get_all_records()
    
    # Overdue detection
    today = datetime.today().strftime('%Y-%m-%d')
    for f in all_followups:
        if f.get('status') not in ['Completed', 'Cancelled'] and f.get('due_date') and f.get('due_date') < today:
            f['is_overdue'] = True
        else:
            f['is_overdue'] = False
            
    if search_query:
        followups = [f for f in all_followups if search_query in f.get('notes', '').lower()]
    else:
        followups = all_followups
        
    return render_template('followups/list.html', followups=followups, search_query=search_query)

@bp.route('/followups/create', methods=['GET', 'POST'])
@login_required
def create_followup():
    if request.method == 'POST':
        data = {
            'notes': request.form.get('notes'),
            'due_date': request.form.get('due_date'),
            'priority': request.form.get('priority', 'Medium'),
            'status': request.form.get('status', 'Pending'),
            'assigned_employee': request.form.get('assigned_employee', ''),
            'customer_id': request.form.get('customer_id', ''),
            'lead_id': request.form.get('lead_id', ''),
            'opportunity_id': request.form.get('opportunity_id', '')
        }
        storage = get_storage('followups')
        storage.create_record(data)
        flash('Follow-up created successfully.', 'success')
        return redirect(url_for('followups.list_followups'))
        
    customers = get_storage('customers').get_all_records()
    leads = get_storage('leads').get_all_records()
    opps = get_storage('opportunities').get_all_records()
    return render_template('followups/create.html', customers=customers, leads=leads, opps=opps)

@bp.route('/followups/<record_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_followup(record_id):
    storage = get_storage('followups')
    followup = storage.get_record(record_id)
    if not followup:
        flash('Follow-up not found.', 'danger')
        return redirect(url_for('followups.list_followups'))
        
    if request.method == 'POST':
        data = {
            'notes': request.form.get('notes'),
            'due_date': request.form.get('due_date'),
            'priority': request.form.get('priority'),
            'status': request.form.get('status'),
            'assigned_employee': request.form.get('assigned_employee'),
            'customer_id': request.form.get('customer_id'),
            'lead_id': request.form.get('lead_id'),
            'opportunity_id': request.form.get('opportunity_id')
        }
        storage.update_record(record_id, data)
        flash('Follow-up updated successfully.', 'success')
        return redirect(url_for('followups.list_followups'))
        
    customers = get_storage('customers').get_all_records()
    leads = get_storage('leads').get_all_records()
    opps = get_storage('opportunities').get_all_records()
    return render_template('followups/edit.html', followup=followup, customers=customers, leads=leads, opps=opps)

@bp.route('/followups/<record_id>/delete', methods=['POST'])
@login_required
def delete_followup(record_id):
    storage = get_storage('followups')
    if storage.delete_record(record_id):
        flash('Follow-up deleted successfully.', 'success')
    else:
        flash('Follow-up not found.', 'danger')
    return redirect(url_for('followups.list_followups'))
''')

# --- TASKS TEMPLATES ---
with open('templates/tasks/list.html', 'w', encoding='utf-8') as f:
    f.write('''{% extends "base/base.html" %}
{% block title %}Tasks - SimpleCRM{% endblock %}
{% block content %}
<div class="card" style="display: flex; justify-content: space-between; align-items: center;">
    <h1>Tasks</h1>
    <a href="{{ url_for('tasks.create_task') }}" class="btn btn-primary">Add Task</a>
</div>

<div class="card">
    <table style="width: 100%; border-collapse: collapse;">
        <thead>
            <tr style="border-bottom: 2px solid var(--border-color); text-align: left;">
                <th style="padding: 0.75rem;">Description</th>
                <th style="padding: 0.75rem;">Due Date</th>
                <th style="padding: 0.75rem;">Status</th>
                <th style="padding: 0.75rem;">Priority</th>
                <th style="padding: 0.75rem;">Actions</th>
            </tr>
        </thead>
        <tbody>
            {% for task in tasks %}
            <tr style="border-bottom: 1px solid var(--border-color);">
                <td style="padding: 0.75rem;">
                    {% if task.is_overdue %}<span style="color: var(--danger-color); font-weight: bold;">[OVERDUE]</span>{% endif %}
                    {{ task.description }}
                </td>
                <td style="padding: 0.75rem; {% if task.is_overdue %}color: var(--danger-color); font-weight:bold;{% endif %}">{{ task.due_date }}</td>
                <td style="padding: 0.75rem;">{{ task.status }}</td>
                <td style="padding: 0.75rem;">{{ task.priority }}</td>
                <td style="padding: 0.75rem; display: flex; gap: 0.5rem;">
                    <a href="{{ url_for('tasks.edit_task', record_id=task.id) }}" style="color: var(--primary-color); text-decoration: none;">Edit</a>
                    <form method="POST" action="{{ url_for('tasks.delete_task', record_id=task.id) }}" style="display:inline;">
                        <button type="submit" style="background:none; border:none; color:var(--danger-color); cursor:pointer; text-decoration:underline;">Delete</button>
                    </form>
                </td>
            </tr>
            {% else %}
            <tr><td colspan="5" style="padding: 1rem; text-align: center;">No tasks found.</td></tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}
''')

# --- UPDATE APP INIT ---
content = """import os
from flask import Flask, session
from config.settings import config
from app.utils.logger import setup_logger

def create_app(config_name='default'):
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Set up logger
    setup_logger(app)
    
    # Ensure data directory exists
    os.makedirs(app.config['DATA_DIR'], exist_ok=True)
    
    # Register blueprints
    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)
    
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from app.dashboard import bp as dashboard_bp
    app.register_blueprint(dashboard_bp)
    
    from app.users import bp as users_bp
    app.register_blueprint(users_bp)
    
    from app.customers import bp as customers_bp
    app.register_blueprint(customers_bp)

    from app.contacts import bp as contacts_bp
    app.register_blueprint(contacts_bp)

    from app.leads import bp as leads_bp
    app.register_blueprint(leads_bp)

    from app.opportunities import bp as opportunities_bp
    app.register_blueprint(opportunities_bp)

    from app.tasks import bp as tasks_bp
    app.register_blueprint(tasks_bp)

    from app.followups import bp as followups_bp
    app.register_blueprint(followups_bp)

    return app
"""
with open('app/__init__.py', 'w', encoding='utf-8') as f:
    f.write(content)

# --- UPDATE BASE TEMPLATE NAV ---
with open('templates/base/base.html', 'r', encoding='utf-8') as f:
    base_html = f.read()

if 'href="/tasks"' not in base_html:
    nav_link = '''<li><a href="{{ url_for('tasks.list_tasks') }}">Tasks</a></li>
                    <li><a href="{{ url_for('followups.list_followups') }}">Follow-ups</a></li>
                    <!-- Future links will go here -->'''
    base_html = base_html.replace('<!-- Future links will go here -->', nav_link)
    with open('templates/base/base.html', 'w', encoding='utf-8') as f:
        f.write(base_html)
