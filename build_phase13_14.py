import os

# --- SETUP DIRECTORIES ---
os.makedirs('app/notes', exist_ok=True)
os.makedirs('templates/notes', exist_ok=True)

# --- NOTES BLUEPRINT ---
with open('app/notes/__init__.py', 'w', encoding='utf-8') as f:
    f.write('''from flask import Blueprint
bp = Blueprint('notes', __name__)
from app.notes import routes
''')

with open('app/notes/routes.py', 'w', encoding='utf-8') as f:
    f.write('''from flask import render_template, request, redirect, url_for, flash, current_app, session
from app.notes import bp
from app.auth.utils import login_required
from app.utils.storage import BaseStorage

def get_storage(name):
    return BaseStorage(current_app.config['DATA_DIR'], name)

@bp.route('/notes')
@login_required
def list_notes():
    storage = get_storage('notes')
    search_query = request.args.get('q', '').lower()
    all_notes = storage.get_all_records()
    
    if search_query:
        notes = [n for n in all_notes if search_query in n.get('content', '').lower() or search_query in n.get('entity_type', '').lower()]
    else:
        notes = all_notes
        
    return render_template('notes/list.html', notes=notes, search_query=search_query)

@bp.route('/notes/create', methods=['POST'])
@login_required
def create_note():
    entity_type = request.form.get('entity_type')
    entity_id = request.form.get('entity_id')
    content = request.form.get('content')
    return_url = request.form.get('return_url', url_for('notes.list_notes'))
    
    if not content:
        flash('Note content cannot be empty.', 'danger')
        return redirect(return_url)
        
    storage = get_storage('notes')
    storage.create_record({
        'entity_type': entity_type,
        'entity_id': entity_id,
        'content': content,
        'author': session.get('username')
    })
    
    flash('Note added successfully.', 'success')
    return redirect(return_url)

@bp.route('/notes/<record_id>/delete', methods=['POST'])
@login_required
def delete_note(record_id):
    storage = get_storage('notes')
    return_url = request.form.get('return_url', url_for('notes.list_notes'))
    if storage.delete_record(record_id):
        flash('Note deleted.', 'success')
    else:
        flash('Note not found.', 'danger')
    return redirect(return_url)
''')

with open('templates/notes/list.html', 'w', encoding='utf-8') as f:
    f.write('''{% extends "base/base.html" %}
{% block title %}Notes - SimpleCRM{% endblock %}
{% block content %}
<div class="card">
    <h1>All Notes</h1>
</div>
<div class="card">
    <form method="GET" action="{{ url_for('notes.list_notes') }}" style="margin-bottom: 1.5rem; display: flex; gap: 1rem;">
        <input type="text" name="q" value="{{ search_query }}" placeholder="Search notes..." style="flex-grow: 1; padding: 0.5rem; border: 1px solid var(--border-color); border-radius: 0.25rem;">
        <button type="submit" class="btn btn-primary">Search</button>
    </form>
    <table style="width: 100%; border-collapse: collapse;">
        <thead>
            <tr style="border-bottom: 2px solid var(--border-color); text-align: left;">
                <th style="padding: 0.75rem;">Date</th>
                <th style="padding: 0.75rem;">Type</th>
                <th style="padding: 0.75rem;">Author</th>
                <th style="padding: 0.75rem;">Content</th>
                <th style="padding: 0.75rem;">Actions</th>
            </tr>
        </thead>
        <tbody>
            {% for n in notes %}
            <tr style="border-bottom: 1px solid var(--border-color);">
                <td style="padding: 0.75rem;">{{ n.created_at[:10] }}</td>
                <td style="padding: 0.75rem;">{{ n.entity_type }}</td>
                <td style="padding: 0.75rem;">{{ n.author }}</td>
                <td style="padding: 0.75rem;">{{ n.content[:50] }}{% if n.content|length > 50 %}...{% endif %}</td>
                <td style="padding: 0.75rem;">
                    <form method="POST" action="{{ url_for('notes.delete_note', record_id=n.id) }}" style="display:inline;">
                        <button type="submit" style="background:none; border:none; color:var(--danger-color); cursor:pointer;">Delete</button>
                    </form>
                </td>
            </tr>
            {% else %}
            <tr><td colspan="5" style="padding: 1rem; text-align: center;">No notes found.</td></tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}
''')


# --- UPDATE DASHBOARD LOGIC ---
with open('app/dashboard/routes.py', 'w', encoding='utf-8') as f:
    f.write('''from flask import render_template, current_app
from app.dashboard import bp
from app.auth.utils import login_required
from app.utils.storage import BaseStorage
from datetime import datetime

def get_storage(name):
    return BaseStorage(current_app.config['DATA_DIR'], name)

@bp.route('/')
@login_required
def index():
    # Gather metrics
    today = datetime.today().strftime('%Y-%m-%d')
    
    customers = get_storage('customers').get_all_records()
    total_customers = len(customers)
    new_customers = len([c for c in customers if c.get('created_at', '').startswith(today)])
    
    leads = get_storage('leads').get_all_records()
    total_leads = len(leads)
    qualified_leads = len([l for l in leads if l.get('status') == 'Qualified'])
    
    opportunities = get_storage('opportunities').get_all_records()
    open_opps = len([o for o in opportunities if o.get('stage') not in ['Won', 'Lost']])
    won_opps = len([o for o in opportunities if o.get('stage') == 'Won'])
    
    sales = get_storage('sales').get_all_records()
    total_sales = sum([float(s.get('total', 0)) for s in sales])
    
    invoices = get_storage('invoices').get_all_records()
    pending_invoices = len([i for i in invoices if i.get('status') == 'Sent'])
    paid_invoices = len([i for i in invoices if i.get('status') == 'Paid'])
    overdue_invoices = len([i for i in invoices if i.get('status') not in ['Paid', 'Cancelled'] and i.get('due_date', '') < today])
    
    tasks = get_storage('tasks').get_all_records()
    pending_tasks = len([t for t in tasks if t.get('status') in ['Pending', 'In Progress']])
    completed_tasks = len([t for t in tasks if t.get('status') == 'Completed'])
    
    followups = get_storage('followups').get_all_records()
    due_followups = len([f for f in followups if f.get('due_date', '') == today and f.get('status') != 'Completed'])
    overdue_followups = len([f for f in followups if f.get('due_date', '') < today and f.get('status') != 'Completed'])
    
    metrics = {
        'total_customers': total_customers, 'new_customers': new_customers,
        'total_leads': total_leads, 'qualified_leads': qualified_leads,
        'open_opps': open_opps, 'won_opps': won_opps,
        'total_sales': total_sales,
        'pending_invoices': pending_invoices, 'paid_invoices': paid_invoices, 'overdue_invoices': overdue_invoices,
        'pending_tasks': pending_tasks, 'completed_tasks': completed_tasks,
        'due_followups': due_followups, 'overdue_followups': overdue_followups
    }
    return render_template('dashboard/index.html', metrics=metrics)
''')

# --- UPDATE DASHBOARD TEMPLATE ---
with open('templates/dashboard/index.html', 'w', encoding='utf-8') as f:
    f.write('''{% extends "base/base.html" %}
{% block title %}Dashboard - SimpleCRM{% endblock %}
{% block content %}
<div class="card" style="margin-bottom: 1rem; padding: 1rem 1.5rem;">
    <h2>Dashboard Overview</h2>
    <p style="color: var(--text-muted);">Welcome back, {{ session.get('username') }}!</p>
</div>

<!-- Main Metrics Grid -->
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; margin-bottom: 1.5rem;">
    <div class="card" style="border-left: 4px solid var(--primary-color);">
        <h4 style="color: var(--text-muted); margin-bottom: 0.5rem;">Customers</h4>
        <div style="font-size: 2rem; font-weight: bold;">{{ metrics.total_customers }}</div>
        <div style="font-size: 0.85rem; color: var(--success-color);">+{{ metrics.new_customers }} today</div>
    </div>
    
    <div class="card" style="border-left: 4px solid var(--warning-color);">
        <h4 style="color: var(--text-muted); margin-bottom: 0.5rem;">Leads</h4>
        <div style="font-size: 2rem; font-weight: bold;">{{ metrics.total_leads }}</div>
        <div style="font-size: 0.85rem; color: var(--text-muted);">{{ metrics.qualified_leads }} Qualified</div>
    </div>
    
    <div class="card" style="border-left: 4px solid #8b5cf6;">
        <h4 style="color: var(--text-muted); margin-bottom: 0.5rem;">Opportunities</h4>
        <div style="font-size: 2rem; font-weight: bold;">{{ metrics.open_opps }}</div>
        <div style="font-size: 0.85rem; color: var(--success-color);">{{ metrics.won_opps }} Won</div>
    </div>
    
    <div class="card" style="border-left: 4px solid var(--success-color);">
        <h4 style="color: var(--text-muted); margin-bottom: 0.5rem;">Total Sales</h4>
        <div style="font-size: 2rem; font-weight: bold;">${{ "%.2f"|format(metrics.total_sales) }}</div>
    </div>
</div>

<!-- Secondary Metrics Grid -->
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1rem;">
    
    <div class="card">
        <h3 style="border-bottom: 1px solid var(--border-color); padding-bottom: 0.5rem; margin-bottom: 1rem;">Invoices</h3>
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
            <span>Pending</span><span style="font-weight:bold;">{{ metrics.pending_invoices }}</span>
        </div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
            <span>Paid</span><span style="font-weight:bold; color:var(--success-color);">{{ metrics.paid_invoices }}</span>
        </div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
            <span>Overdue</span><span style="font-weight:bold; color:var(--danger-color);">{{ metrics.overdue_invoices }}</span>
        </div>
        
        <!-- Simple CSS Bar Chart for Invoices -->
        {% set total_inv = metrics.pending_invoices + metrics.paid_invoices + metrics.overdue_invoices %}
        {% if total_inv > 0 %}
        <div style="width: 100%; height: 10px; display: flex; border-radius: 5px; overflow: hidden; margin-top:1rem;">
            <div style="width: {{ (metrics.paid_invoices / total_inv) * 100 }}%; background: var(--success-color);"></div>
            <div style="width: {{ (metrics.pending_invoices / total_inv) * 100 }}%; background: var(--warning-color);"></div>
            <div style="width: {{ (metrics.overdue_invoices / total_inv) * 100 }}%; background: var(--danger-color);"></div>
        </div>
        {% endif %}
    </div>
    
    <div class="card">
        <h3 style="border-bottom: 1px solid var(--border-color); padding-bottom: 0.5rem; margin-bottom: 1rem;">Tasks & Follow-ups</h3>
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
            <span>Pending Tasks</span><span style="font-weight:bold;">{{ metrics.pending_tasks }}</span>
        </div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
            <span>Completed Tasks</span><span style="font-weight:bold; color:var(--success-color);">{{ metrics.completed_tasks }}</span>
        </div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
            <span>Follow-ups Due Today</span><span style="font-weight:bold; color:var(--warning-color);">{{ metrics.due_followups }}</span>
        </div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
            <span>Overdue Follow-ups</span><span style="font-weight:bold; color:var(--danger-color);">{{ metrics.overdue_followups }}</span>
        </div>
    </div>
    
</div>
{% endblock %}
''')

# --- INJECT NOTES INTO CUSTOMER VIEW ---
with open('templates/customers/view.html', 'r', encoding='utf-8') as f:
    c_view = f.read()

notes_snippet = '''
<div class="card" style="margin-top: 1.5rem;">
    <h2>Customer Notes & History</h2>
    
    <form method="POST" action="{{ url_for('notes.create_note') }}" style="margin-top: 1rem; margin-bottom: 1rem;">
        <input type="hidden" name="entity_type" value="Customer">
        <input type="hidden" name="entity_id" value="{{ customer.id }}">
        <input type="hidden" name="return_url" value="{{ request.url }}">
        <div style="display: flex; gap: 0.5rem;">
            <input type="text" name="content" required placeholder="Add a note..." style="flex-grow: 1; padding: 0.5rem; border: 1px solid var(--border-color); border-radius: 0.25rem;">
            <button type="submit" class="btn btn-primary">Add Note</button>
        </div>
    </form>
    
    <div style="border-top: 1px solid var(--border-color); padding-top: 1rem;">
        <p style="color: var(--text-muted); font-size: 0.9rem;">(Notes will appear in the Notes module)</p>
        <a href="{{ url_for('notes.list_notes') }}?q=Customer" class="btn" style="background: var(--bg-color);">View all Customer Notes</a>
    </div>
</div>
'''

if 'Customer Notes & History' not in c_view:
    c_view = c_view.replace('{% endblock %}', notes_snippet + '\n{% endblock %}')
    with open('templates/customers/view.html', 'w', encoding='utf-8') as f:
        f.write(c_view)

# --- UPDATE APP INIT ---
content = """import os
from flask import Flask, session
from config.settings import config
from app.utils.logger import setup_logger

def create_app(config_name='default'):
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config.from_object(config[config_name])
    setup_logger(app)
    os.makedirs(app.config['DATA_DIR'], exist_ok=True)
    
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
    from app.products import bp as products_bp
    app.register_blueprint(products_bp)
    from app.sales import bp as sales_bp
    app.register_blueprint(sales_bp)
    from app.invoices import bp as invoices_bp
    app.register_blueprint(invoices_bp)
    from app.payments import bp as payments_bp
    app.register_blueprint(payments_bp)
    from app.notes import bp as notes_bp
    app.register_blueprint(notes_bp)

    return app
"""
with open('app/__init__.py', 'w', encoding='utf-8') as f:
    f.write(content)

# --- UPDATE BASE TEMPLATE NAV ---
with open('templates/base/base.html', 'r', encoding='utf-8') as f:
    base_html = f.read()

if 'href="/notes"' not in base_html:
    nav_link = '''<li><a href="{{ url_for('notes.list_notes') }}">Notes</a></li>
                    <!-- Future links will go here -->'''
    base_html = base_html.replace('<!-- Future links will go here -->', nav_link)
    with open('templates/base/base.html', 'w', encoding='utf-8') as f:
        f.write(base_html)
