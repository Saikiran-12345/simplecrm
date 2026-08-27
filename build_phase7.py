import os

os.makedirs('app/opportunities', exist_ok=True)
os.makedirs('templates/opportunities', exist_ok=True)

with open('app/opportunities/__init__.py', 'w', encoding='utf-8') as f:
    f.write('''from flask import Blueprint
bp = Blueprint('opportunities', __name__)
from app.opportunities import routes
''')

with open('app/opportunities/routes.py', 'w', encoding='utf-8') as f:
    f.write('''from flask import render_template, request, redirect, url_for, flash, current_app
from app.opportunities import bp
from app.auth.utils import login_required
from app.utils.storage import BaseStorage

def get_storage(name):
    return BaseStorage(current_app.config['DATA_DIR'], name)

@bp.route('/opportunities')
@login_required
def list_opportunities():
    storage = get_storage('opportunities')
    cust_storage = get_storage('customers')
    lead_storage = get_storage('leads')
    
    search_query = request.args.get('q', '').lower()
    
    all_opps = storage.get_all_records()
    
    # Map associations
    for opp in all_opps:
        if opp.get('customer_id'):
            c = cust_storage.get_record(opp['customer_id'])
            opp['associated_name'] = f"Customer: {c.get('first_name')} {c.get('last_name')}" if c else "Unknown Customer"
        elif opp.get('lead_id'):
            l = lead_storage.get_record(opp['lead_id'])
            opp['associated_name'] = f"Lead: {l.get('name')}" if l else "Unknown Lead"
        else:
            opp['associated_name'] = "None"
            
        # Calculate expected value (Value * Probability / 100)
        try:
            val = float(opp.get('value', 0))
            prob = float(opp.get('probability', 0))
            opp['weighted_value'] = val * (prob / 100)
        except ValueError:
            opp['weighted_value'] = 0.0

    if search_query:
        opps = [o for o in all_opps if search_query in o.get('title', '').lower() or 
                search_query in o.get('associated_name', '').lower()]
    else:
        opps = all_opps
        
    return render_template('opportunities/list.html', opportunities=opps, search_query=search_query)

@bp.route('/opportunities/create', methods=['GET', 'POST'])
@login_required
def create_opportunity():
    customers = get_storage('customers').get_all_records()
    leads = get_storage('leads').get_all_records()
    
    if request.method == 'POST':
        data = {
            'title': request.form.get('title'),
            'description': request.form.get('description'),
            'value': request.form.get('value', '0'),
            'probability': request.form.get('probability', '0'),
            'stage': request.form.get('stage', 'New'),
            'expected_close_date': request.form.get('expected_close_date'),
            'assigned_employee': request.form.get('assigned_employee', ''),
            'customer_id': request.form.get('customer_id'),
            'lead_id': request.form.get('lead_id')
        }
        storage = get_storage('opportunities')
        storage.create_record(data)
        flash('Opportunity created successfully.', 'success')
        return redirect(url_for('opportunities.list_opportunities'))
        
    return render_template('opportunities/create.html', customers=customers, leads=leads)

@bp.route('/opportunities/<record_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_opportunity(record_id):
    storage = get_storage('opportunities')
    opp = storage.get_record(record_id)
    if not opp:
        flash('Opportunity not found.', 'danger')
        return redirect(url_for('opportunities.list_opportunities'))
        
    customers = get_storage('customers').get_all_records()
    leads = get_storage('leads').get_all_records()
        
    if request.method == 'POST':
        data = {
            'title': request.form.get('title'),
            'description': request.form.get('description'),
            'value': request.form.get('value'),
            'probability': request.form.get('probability'),
            'stage': request.form.get('stage'),
            'expected_close_date': request.form.get('expected_close_date'),
            'assigned_employee': request.form.get('assigned_employee'),
            'customer_id': request.form.get('customer_id'),
            'lead_id': request.form.get('lead_id')
        }
        storage.update_record(record_id, data)
        flash('Opportunity updated successfully.', 'success')
        return redirect(url_for('opportunities.list_opportunities'))
        
    return render_template('opportunities/edit.html', opportunity=opp, customers=customers, leads=leads)

@bp.route('/opportunities/<record_id>/delete', methods=['POST'])
@login_required
def delete_opportunity(record_id):
    storage = get_storage('opportunities')
    if storage.delete_record(record_id):
        flash('Opportunity deleted successfully.', 'success')
    else:
        flash('Opportunity not found.', 'danger')
    return redirect(url_for('opportunities.list_opportunities'))
''')

with open('templates/opportunities/list.html', 'w', encoding='utf-8') as f:
    f.write('''{% extends "base/base.html" %}
{% block title %}Opportunities - SimpleCRM{% endblock %}
{% block content %}
<div class="card" style="display: flex; justify-content: space-between; align-items: center;">
    <h1>Opportunities</h1>
    <a href="{{ url_for('opportunities.create_opportunity') }}" class="btn btn-primary">Add Opportunity</a>
</div>

<div class="card">
    <form method="GET" action="{{ url_for('opportunities.list_opportunities') }}" style="margin-bottom: 1.5rem; display: flex; gap: 1rem;">
        <input type="text" name="q" value="{{ search_query }}" placeholder="Search opportunities..." style="flex-grow: 1; padding: 0.5rem; border: 1px solid var(--border-color); border-radius: 0.25rem;">
        <button type="submit" class="btn btn-primary">Search</button>
        {% if search_query %}
            <a href="{{ url_for('opportunities.list_opportunities') }}" class="btn" style="background: var(--border-color);">Clear</a>
        {% endif %}
    </form>

    <table style="width: 100%; border-collapse: collapse;">
        <thead>
            <tr style="border-bottom: 2px solid var(--border-color); text-align: left;">
                <th style="padding: 0.75rem;">Title</th>
                <th style="padding: 0.75rem;">Associated With</th>
                <th style="padding: 0.75rem;">Stage</th>
                <th style="padding: 0.75rem;">Value</th>
                <th style="padding: 0.75rem;">Weighted</th>
                <th style="padding: 0.75rem;">Actions</th>
            </tr>
        </thead>
        <tbody>
            {% for opp in opportunities %}
            <tr style="border-bottom: 1px solid var(--border-color);">
                <td style="padding: 0.75rem; font-weight: 500;">{{ opp.title }}</td>
                <td style="padding: 0.75rem; font-size: 0.9em; color: var(--secondary-color);">{{ opp.associated_name }}</td>
                <td style="padding: 0.75rem;">
                    <span style="padding: 0.25rem 0.5rem; border-radius: 9999px; font-size: 0.875rem; 
                    background-color: {% if opp.stage == 'Won' %}#dcfce7; color: #166534;{% elif opp.stage == 'Lost' %}#fee2e2; color: #991b1b;{% else %}#e0f2fe; color: #0369a1;{% endif %}">
                        {{ opp.stage }}
                    </span>
                </td>
                <td style="padding: 0.75rem;">${{ opp.value }} ({{ opp.probability }}%)</td>
                <td style="padding: 0.75rem;">${{ "%.2f"|format(opp.weighted_value) }}</td>
                <td style="padding: 0.75rem; display: flex; gap: 0.5rem;">
                    <a href="{{ url_for('opportunities.edit_opportunity', record_id=opp.id) }}" style="color: var(--primary-color); text-decoration: none;">Edit</a>
                    <form method="POST" action="{{ url_for('opportunities.delete_opportunity', record_id=opp.id) }}" style="display:inline;">
                        <button type="submit" style="background:none; border:none; color:var(--danger-color); cursor:pointer; text-decoration:underline;">Delete</button>
                    </form>
                </td>
            </tr>
            {% else %}
            <tr>
                <td colspan="6" style="padding: 1rem; text-align: center; color: var(--text-muted);">No opportunities found.</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}
''')

form_template_content = '''
<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
    <div class="form-group" style="margin-bottom: 1rem; grid-column: span 2;">
        <label style="display: block; margin-bottom: 0.5rem;">Opportunity Title</label>
        <input type="text" name="title" value="{{ opportunity.title if opportunity else '' }}" required style="width: 100%; padding: 0.5rem; border: 1px solid var(--border-color); border-radius: 0.25rem;">
    </div>
    <div class="form-group" style="margin-bottom: 1rem; grid-column: span 2;">
        <label style="display: block; margin-bottom: 0.5rem;">Description</label>
        <textarea name="description" rows="3" style="width: 100%; padding: 0.5rem; border: 1px solid var(--border-color); border-radius: 0.25rem;">{{ opportunity.description if opportunity else '' }}</textarea>
    </div>
    
    <div class="form-group" style="margin-bottom: 1rem;">
        <label style="display: block; margin-bottom: 0.5rem;">Customer (Optional)</label>
        <select name="customer_id" style="width: 100%; padding: 0.5rem; border: 1px solid var(--border-color); border-radius: 0.25rem;">
            <option value="">-- None --</option>
            {% for customer in customers %}
            <option value="{{ customer.id }}" {% if opportunity and opportunity.customer_id == customer.id %}selected{% endif %}>
                {{ customer.first_name }} {{ customer.last_name }} ({{ customer.company }})
            </option>
            {% endfor %}
        </select>
    </div>
    
    <div class="form-group" style="margin-bottom: 1rem;">
        <label style="display: block; margin-bottom: 0.5rem;">Lead (Optional)</label>
        <select name="lead_id" style="width: 100%; padding: 0.5rem; border: 1px solid var(--border-color); border-radius: 0.25rem;">
            <option value="">-- None --</option>
            {% for lead in leads %}
            <option value="{{ lead.id }}" {% if opportunity and opportunity.lead_id == lead.id %}selected{% endif %}>
                {{ lead.name }} ({{ lead.company }})
            </option>
            {% endfor %}
        </select>
    </div>

    <div class="form-group" style="margin-bottom: 1rem;">
        <label style="display: block; margin-bottom: 0.5rem;">Value ($)</label>
        <input type="number" step="0.01" name="value" value="{{ opportunity.value if opportunity else '0' }}" style="width: 100%; padding: 0.5rem; border: 1px solid var(--border-color); border-radius: 0.25rem;">
    </div>
    
    <div class="form-group" style="margin-bottom: 1rem;">
        <label style="display: block; margin-bottom: 0.5rem;">Probability (%)</label>
        <input type="number" step="1" min="0" max="100" name="probability" value="{{ opportunity.probability if opportunity else '50' }}" style="width: 100%; padding: 0.5rem; border: 1px solid var(--border-color); border-radius: 0.25rem;">
    </div>
    
    <div class="form-group" style="margin-bottom: 1rem;">
        <label style="display: block; margin-bottom: 0.5rem;">Stage</label>
        <select name="stage" style="width: 100%; padding: 0.5rem; border: 1px solid var(--border-color); border-radius: 0.25rem;">
            {% for s in ['New', 'Qualification', 'Proposal', 'Negotiation', 'Won', 'Lost'] %}
                <option value="{{ s }}" {% if opportunity and opportunity.stage == s %}selected{% endif %}>{{ s }}</option>
            {% endfor %}
        </select>
    </div>
    
    <div class="form-group" style="margin-bottom: 1rem;">
        <label style="display: block; margin-bottom: 0.5rem;">Expected Close Date</label>
        <input type="date" name="expected_close_date" value="{{ opportunity.expected_close_date if opportunity else '' }}" style="width: 100%; padding: 0.5rem; border: 1px solid var(--border-color); border-radius: 0.25rem;">
    </div>
</div>
'''

with open('templates/opportunities/create.html', 'w', encoding='utf-8') as f:
    f.write('''{% extends "base/base.html" %}
{% block title %}Add Opportunity - SimpleCRM{% endblock %}
{% block content %}
<div class="card">
    <h1>Add New Opportunity</h1>
    <form method="POST" action="{{ url_for('opportunities.create_opportunity') }}" style="max-width: 800px; margin-top: 1.5rem;">
        ''' + form_template_content + '''
        <div style="margin-top: 1.5rem;">
            <button type="submit" class="btn btn-primary">Create Opportunity</button>
            <a href="{{ url_for('opportunities.list_opportunities') }}" class="btn" style="background: var(--border-color);">Cancel</a>
        </div>
    </form>
</div>
{% endblock %}
''')

with open('templates/opportunities/edit.html', 'w', encoding='utf-8') as f:
    f.write('''{% extends "base/base.html" %}
{% block title %}Edit Opportunity - SimpleCRM{% endblock %}
{% block content %}
<div class="card">
    <h1>Edit Opportunity</h1>
    <form method="POST" action="{{ url_for('opportunities.edit_opportunity', record_id=opportunity.id) }}" style="max-width: 800px; margin-top: 1.5rem;">
        ''' + form_template_content + '''
        <div style="margin-top: 1.5rem;">
            <button type="submit" class="btn btn-primary">Save Changes</button>
            <a href="{{ url_for('opportunities.list_opportunities') }}" class="btn" style="background: var(--border-color);">Cancel</a>
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

    from app.opportunities import bp as opportunities_bp
    app.register_blueprint(opportunities_bp)

    return app
"""
with open('app/__init__.py', 'w', encoding='utf-8') as f:
    f.write(content)

# --- UPDATE BASE TEMPLATE NAV ---
with open('templates/base/base.html', 'r', encoding='utf-8') as f:
    base_html = f.read()

if 'href="/opportunities"' not in base_html:
    nav_link = '<li><a href="{{ url_for(\'opportunities.list_opportunities\') }}">Opportunities</a></li>\n                    <!-- Future links will go here -->'
    base_html = base_html.replace('<!-- Future links will go here -->', nav_link)
    with open('templates/base/base.html', 'w', encoding='utf-8') as f:
        f.write(base_html)
