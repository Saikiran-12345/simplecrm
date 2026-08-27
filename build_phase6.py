import os

os.makedirs('app/leads', exist_ok=True)
os.makedirs('templates/leads', exist_ok=True)

with open('app/leads/__init__.py', 'w', encoding='utf-8') as f:
    f.write('''from flask import Blueprint
bp = Blueprint('leads', __name__)
from app.leads import routes
''')

with open('app/leads/routes.py', 'w', encoding='utf-8') as f:
    f.write('''from flask import render_template, request, redirect, url_for, flash, current_app
from app.leads import bp
from app.auth.utils import login_required
from app.utils.storage import BaseStorage
from datetime import datetime

def get_lead_storage():
    return BaseStorage(current_app.config['DATA_DIR'], 'leads')

def get_customer_storage():
    return BaseStorage(current_app.config['DATA_DIR'], 'customers')

@bp.route('/leads')
@login_required
def list_leads():
    storage = get_lead_storage()
    search_query = request.args.get('q', '').lower()
    
    all_leads = storage.get_all_records()
    if search_query:
        leads = [l for l in all_leads if search_query in l.get('name', '').lower() or 
                 search_query in l.get('company', '').lower() or 
                 search_query in l.get('email', '').lower()]
    else:
        leads = all_leads
        
    return render_template('leads/list.html', leads=leads, search_query=search_query)

@bp.route('/leads/create', methods=['GET', 'POST'])
@login_required
def create_lead():
    if request.method == 'POST':
        data = {
            'name': request.form.get('name'),
            'company': request.form.get('company'),
            'email': request.form.get('email'),
            'phone': request.form.get('phone'),
            'source': request.form.get('source'),
            'status': request.form.get('status', 'New'),
            'priority': request.form.get('priority', 'Medium'),
            'assigned_employee': request.form.get('assigned_employee', ''),
            'expected_value': request.form.get('expected_value', '0')
        }
        storage = get_lead_storage()
        storage.create_record(data)
        flash('Lead created successfully.', 'success')
        return redirect(url_for('leads.list_leads'))
        
    return render_template('leads/create.html')

@bp.route('/leads/<record_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_lead(record_id):
    storage = get_lead_storage()
    lead = storage.get_record(record_id)
    if not lead:
        flash('Lead not found.', 'danger')
        return redirect(url_for('leads.list_leads'))
        
    if request.method == 'POST':
        data = {
            'name': request.form.get('name'),
            'company': request.form.get('company'),
            'email': request.form.get('email'),
            'phone': request.form.get('phone'),
            'source': request.form.get('source'),
            'status': request.form.get('status'),
            'priority': request.form.get('priority'),
            'assigned_employee': request.form.get('assigned_employee'),
            'expected_value': request.form.get('expected_value')
        }
        storage.update_record(record_id, data)
        flash('Lead updated successfully.', 'success')
        return redirect(url_for('leads.list_leads'))
        
    return render_template('leads/edit.html', lead=lead)

@bp.route('/leads/<record_id>/convert', methods=['POST'])
@login_required
def convert_lead(record_id):
    storage = get_lead_storage()
    lead = storage.get_record(record_id)
    if not lead:
        flash('Lead not found.', 'danger')
        return redirect(url_for('leads.list_leads'))
        
    if lead.get('status') == 'Converted':
        flash('Lead is already converted.', 'info')
        return redirect(url_for('leads.list_leads'))

    # Create customer from lead
    c_storage = get_customer_storage()
    names = lead.get('name', '').split(' ', 1)
    first_name = names[0] if len(names) > 0 else 'Unknown'
    last_name = names[1] if len(names) > 1 else ''
    
    c_data = {
        'first_name': first_name,
        'last_name': last_name,
        'company': lead.get('company', ''),
        'email': lead.get('email', ''),
        'phone': lead.get('phone', ''),
        'status': 'Active',
        'source': lead.get('source', '')
    }
    customer_id = c_storage.create_record(c_data)
    
    # Update lead status
    storage.update_record(record_id, {'status': 'Converted', 'converted_to_customer_id': customer_id})
    flash('Lead successfully converted to Customer!', 'success')
    return redirect(url_for('customers.view_customer', record_id=customer_id))

@bp.route('/leads/<record_id>/delete', methods=['POST'])
@login_required
def delete_lead(record_id):
    storage = get_lead_storage()
    if storage.delete_record(record_id):
        flash('Lead deleted successfully.', 'success')
    else:
        flash('Lead not found.', 'danger')
    return redirect(url_for('leads.list_leads'))
''')

with open('templates/leads/list.html', 'w', encoding='utf-8') as f:
    f.write('''{% extends "base/base.html" %}
{% block title %}Leads - SimpleCRM{% endblock %}
{% block content %}
<div class="card" style="display: flex; justify-content: space-between; align-items: center;">
    <h1>Leads</h1>
    <a href="{{ url_for('leads.create_lead') }}" class="btn btn-primary">Add Lead</a>
</div>

<div class="card">
    <form method="GET" action="{{ url_for('leads.list_leads') }}" style="margin-bottom: 1.5rem; display: flex; gap: 1rem;">
        <input type="text" name="q" value="{{ search_query }}" placeholder="Search leads..." style="flex-grow: 1; padding: 0.5rem; border: 1px solid var(--border-color); border-radius: 0.25rem;">
        <button type="submit" class="btn btn-primary">Search</button>
        {% if search_query %}
            <a href="{{ url_for('leads.list_leads') }}" class="btn" style="background: var(--border-color);">Clear</a>
        {% endif %}
    </form>

    <table style="width: 100%; border-collapse: collapse;">
        <thead>
            <tr style="border-bottom: 2px solid var(--border-color); text-align: left;">
                <th style="padding: 0.75rem;">Name</th>
                <th style="padding: 0.75rem;">Company</th>
                <th style="padding: 0.75rem;">Status</th>
                <th style="padding: 0.75rem;">Priority</th>
                <th style="padding: 0.75rem;">Actions</th>
            </tr>
        </thead>
        <tbody>
            {% for lead in leads %}
            <tr style="border-bottom: 1px solid var(--border-color);">
                <td style="padding: 0.75rem; font-weight: 500;">{{ lead.name }}</td>
                <td style="padding: 0.75rem;">{{ lead.company }}</td>
                <td style="padding: 0.75rem;">
                    <span style="padding: 0.25rem 0.5rem; border-radius: 9999px; font-size: 0.875rem; background-color: {% if lead.status == 'Converted' %}#dcfce7; color: #166534;{% elif lead.status == 'Lost' %}#fee2e2; color: #991b1b;{% else %}#e0f2fe; color: #0369a1;{% endif %}">
                        {{ lead.status }}
                    </span>
                </td>
                <td style="padding: 0.75rem;">{{ lead.priority }}</td>
                <td style="padding: 0.75rem; display: flex; gap: 0.5rem;">
                    <a href="{{ url_for('leads.edit_lead', record_id=lead.id) }}" style="color: var(--primary-color); text-decoration: none;">Edit</a>
                    {% if lead.status != 'Converted' %}
                    <form method="POST" action="{{ url_for('leads.convert_lead', record_id=lead.id) }}" style="display:inline;">
                        <button type="submit" style="background:none; border:none; color:var(--success-color); cursor:pointer; text-decoration:underline;">Convert</button>
                    </form>
                    {% endif %}
                </td>
            </tr>
            {% else %}
            <tr>
                <td colspan="5" style="padding: 1rem; text-align: center; color: var(--text-muted);">No leads found.</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}
''')

form_template_content = '''
<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
    <div class="form-group" style="margin-bottom: 1rem;">
        <label style="display: block; margin-bottom: 0.5rem;">Lead Name</label>
        <input type="text" name="name" value="{{ lead.name if lead else '' }}" required style="width: 100%; padding: 0.5rem; border: 1px solid var(--border-color); border-radius: 0.25rem;">
    </div>
    <div class="form-group" style="margin-bottom: 1rem;">
        <label style="display: block; margin-bottom: 0.5rem;">Company</label>
        <input type="text" name="company" value="{{ lead.company if lead else '' }}" style="width: 100%; padding: 0.5rem; border: 1px solid var(--border-color); border-radius: 0.25rem;">
    </div>
    <div class="form-group" style="margin-bottom: 1rem;">
        <label style="display: block; margin-bottom: 0.5rem;">Email</label>
        <input type="email" name="email" value="{{ lead.email if lead else '' }}" style="width: 100%; padding: 0.5rem; border: 1px solid var(--border-color); border-radius: 0.25rem;">
    </div>
    <div class="form-group" style="margin-bottom: 1rem;">
        <label style="display: block; margin-bottom: 0.5rem;">Phone</label>
        <input type="text" name="phone" value="{{ lead.phone if lead else '' }}" style="width: 100%; padding: 0.5rem; border: 1px solid var(--border-color); border-radius: 0.25rem;">
    </div>
    <div class="form-group" style="margin-bottom: 1rem;">
        <label style="display: block; margin-bottom: 0.5rem;">Status</label>
        <select name="status" style="width: 100%; padding: 0.5rem; border: 1px solid var(--border-color); border-radius: 0.25rem;">
            {% for s in ['New', 'Contacted', 'Qualified', 'Unqualified', 'Converted', 'Lost'] %}
                <option value="{{ s }}" {% if lead and lead.status == s %}selected{% endif %}>{{ s }}</option>
            {% endfor %}
        </select>
    </div>
    <div class="form-group" style="margin-bottom: 1rem;">
        <label style="display: block; margin-bottom: 0.5rem;">Priority</label>
        <select name="priority" style="width: 100%; padding: 0.5rem; border: 1px solid var(--border-color); border-radius: 0.25rem;">
            {% for p in ['Low', 'Medium', 'High'] %}
                <option value="{{ p }}" {% if lead and lead.priority == p %}selected{% endif %}>{{ p }}</option>
            {% endfor %}
        </select>
    </div>
    <div class="form-group" style="margin-bottom: 1rem;">
        <label style="display: block; margin-bottom: 0.5rem;">Expected Value ($)</label>
        <input type="number" step="0.01" name="expected_value" value="{{ lead.expected_value if lead else '0' }}" style="width: 100%; padding: 0.5rem; border: 1px solid var(--border-color); border-radius: 0.25rem;">
    </div>
</div>
'''

with open('templates/leads/create.html', 'w', encoding='utf-8') as f:
    f.write('''{% extends "base/base.html" %}
{% block title %}Add Lead - SimpleCRM{% endblock %}
{% block content %}
<div class="card">
    <h1>Add New Lead</h1>
    <form method="POST" action="{{ url_for('leads.create_lead') }}" style="max-width: 800px; margin-top: 1.5rem;">
        ''' + form_template_content + '''
        <div style="margin-top: 1.5rem;">
            <button type="submit" class="btn btn-primary">Create Lead</button>
            <a href="{{ url_for('leads.list_leads') }}" class="btn" style="background: var(--border-color);">Cancel</a>
        </div>
    </form>
</div>
{% endblock %}
''')

with open('templates/leads/edit.html', 'w', encoding='utf-8') as f:
    f.write('''{% extends "base/base.html" %}
{% block title %}Edit Lead - SimpleCRM{% endblock %}
{% block content %}
<div class="card">
    <h1>Edit Lead</h1>
    <form method="POST" action="{{ url_for('leads.edit_lead', record_id=lead.id) }}" style="max-width: 800px; margin-top: 1.5rem;">
        ''' + form_template_content + '''
        <div style="margin-top: 1.5rem;">
            <button type="submit" class="btn btn-primary">Save Changes</button>
            <a href="{{ url_for('leads.list_leads') }}" class="btn" style="background: var(--border-color);">Cancel</a>
        </div>
    </form>
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

    return app
"""
with open('app/__init__.py', 'w', encoding='utf-8') as f:
    f.write(content)

# --- UPDATE BASE TEMPLATE NAV ---
with open('templates/base/base.html', 'r', encoding='utf-8') as f:
    base_html = f.read()

if 'href="/leads"' not in base_html:
    nav_link = '<li><a href="{{ url_for(\'leads.list_leads\') }}">Leads</a></li>\n                    <!-- Future links will go here -->'
    base_html = base_html.replace('<!-- Future links will go here -->', nav_link)
    with open('templates/base/base.html', 'w', encoding='utf-8') as f:
        f.write(base_html)
