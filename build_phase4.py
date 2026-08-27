import os
import re

# --- CUSTOMERS BLUEPRINT ---
os.makedirs('app/customers', exist_ok=True)
os.makedirs('templates/customers', exist_ok=True)

with open('app/customers/__init__.py', 'w', encoding='utf-8') as f:
    f.write('''from flask import Blueprint
bp = Blueprint('customers', __name__)
from app.customers import routes
''')

with open('app/customers/routes.py', 'w', encoding='utf-8') as f:
    f.write('''from flask import render_template, request, redirect, url_for, flash, current_app
from app.customers import bp
from app.auth.utils import login_required
from app.utils.storage import BaseStorage

def get_customer_storage():
    return BaseStorage(current_app.config['DATA_DIR'], 'customers')

@bp.route('/customers')
@login_required
def list_customers():
    storage = get_customer_storage()
    search_query = request.args.get('q', '').lower()
    
    all_customers = storage.get_all_records()
    if search_query:
        customers = [c for c in all_customers if search_query in c.get('first_name', '').lower() or 
                     search_query in c.get('last_name', '').lower() or 
                     search_query in c.get('company', '').lower() or
                     search_query in c.get('email', '').lower()]
    else:
        customers = all_customers
        
    return render_template('customers/list.html', customers=customers, search_query=search_query)

@bp.route('/customers/create', methods=['GET', 'POST'])
@login_required
def create_customer():
    if request.method == 'POST':
        data = {
            'first_name': request.form.get('first_name'),
            'last_name': request.form.get('last_name'),
            'company': request.form.get('company'),
            'email': request.form.get('email'),
            'phone': request.form.get('phone'),
            'address': request.form.get('address'),
            'city': request.form.get('city'),
            'state': request.form.get('state'),
            'country': request.form.get('country'),
            'customer_type': request.form.get('customer_type'),
            'status': request.form.get('status'),
            'source': request.form.get('source'),
            'assigned_employee': request.form.get('assigned_employee', '')
        }
        storage = get_customer_storage()
        storage.create_record(data)
        flash('Customer created successfully.', 'success')
        return redirect(url_for('customers.list_customers'))
        
    return render_template('customers/create.html')

@bp.route('/customers/<record_id>')
@login_required
def view_customer(record_id):
    storage = get_customer_storage()
    customer = storage.get_record(record_id)
    if not customer:
        flash('Customer not found.', 'danger')
        return redirect(url_for('customers.list_customers'))
        
    return render_template('customers/view.html', customer=customer)

@bp.route('/customers/<record_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_customer(record_id):
    storage = get_customer_storage()
    customer = storage.get_record(record_id)
    if not customer:
        flash('Customer not found.', 'danger')
        return redirect(url_for('customers.list_customers'))
        
    if request.method == 'POST':
        data = {
            'first_name': request.form.get('first_name'),
            'last_name': request.form.get('last_name'),
            'company': request.form.get('company'),
            'email': request.form.get('email'),
            'phone': request.form.get('phone'),
            'address': request.form.get('address'),
            'city': request.form.get('city'),
            'state': request.form.get('state'),
            'country': request.form.get('country'),
            'customer_type': request.form.get('customer_type'),
            'status': request.form.get('status'),
            'source': request.form.get('source'),
            'assigned_employee': request.form.get('assigned_employee', '')
        }
        storage.update_record(record_id, data)
        flash('Customer updated successfully.', 'success')
        return redirect(url_for('customers.view_customer', record_id=record_id))
        
    return render_template('customers/edit.html', customer=customer)

@bp.route('/customers/<record_id>/delete', methods=['POST'])
@login_required
def delete_customer(record_id):
    storage = get_customer_storage()
    if storage.delete_record(record_id):
        flash('Customer deleted successfully.', 'success')
    else:
        flash('Customer not found or could not be deleted.', 'danger')
    return redirect(url_for('customers.list_customers'))
''')

# --- TEMPLATES ---
with open('templates/customers/list.html', 'w', encoding='utf-8') as f:
    f.write('''{% extends "base/base.html" %}
{% block title %}Customers - SimpleCRM{% endblock %}
{% block content %}
<div class="card" style="display: flex; justify-content: space-between; align-items: center;">
    <h1>Customers</h1>
    <a href="{{ url_for('customers.create_customer') }}" class="btn btn-primary">Add Customer</a>
</div>

<div class="card">
    <form method="GET" action="{{ url_for('customers.list_customers') }}" style="margin-bottom: 1.5rem; display: flex; gap: 1rem;">
        <input type="text" name="q" value="{{ search_query }}" placeholder="Search by name, company, email..." style="flex-grow: 1; padding: 0.5rem; border: 1px solid var(--border-color); border-radius: 0.25rem;">
        <button type="submit" class="btn btn-primary">Search</button>
        {% if search_query %}
            <a href="{{ url_for('customers.list_customers') }}" class="btn" style="background: var(--border-color);">Clear</a>
        {% endif %}
    </form>

    <table style="width: 100%; border-collapse: collapse;">
        <thead>
            <tr style="border-bottom: 2px solid var(--border-color); text-align: left;">
                <th style="padding: 0.75rem;">Name</th>
                <th style="padding: 0.75rem;">Company</th>
                <th style="padding: 0.75rem;">Email</th>
                <th style="padding: 0.75rem;">Status</th>
                <th style="padding: 0.75rem;">Actions</th>
            </tr>
        </thead>
        <tbody>
            {% for customer in customers %}
            <tr style="border-bottom: 1px solid var(--border-color);">
                <td style="padding: 0.75rem;">
                    <a href="{{ url_for('customers.view_customer', record_id=customer.id) }}" style="color: var(--text-main); font-weight: 500;">
                        {{ customer.first_name }} {{ customer.last_name }}
                    </a>
                </td>
                <td style="padding: 0.75rem;">{{ customer.company }}</td>
                <td style="padding: 0.75rem;">{{ customer.email }}</td>
                <td style="padding: 0.75rem;">
                    <span style="padding: 0.25rem 0.5rem; border-radius: 9999px; font-size: 0.875rem; background-color: {% if customer.status == 'Active' %}#dcfce7; color: #166534;{% else %}#fee2e2; color: #991b1b;{% endif %}">
                        {{ customer.status }}
                    </span>
                </td>
                <td style="padding: 0.75rem;">
                    <a href="{{ url_for('customers.edit_customer', record_id=customer.id) }}" style="color: var(--primary-color); text-decoration: none; margin-right: 0.5rem;">Edit</a>
                </td>
            </tr>
            {% else %}
            <tr>
                <td colspan="5" style="padding: 1rem; text-align: center; color: var(--text-muted);">No customers found.</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}
''')

form_template_content = '''
<div class="form-group" style="margin-bottom: 1rem;">
    <label style="display: block; margin-bottom: 0.5rem;">First Name</label>
    <input type="text" name="first_name" value="{{ customer.first_name if customer else '' }}" required style="width: 100%; padding: 0.5rem; border: 1px solid var(--border-color); border-radius: 0.25rem;">
</div>
<div class="form-group" style="margin-bottom: 1rem;">
    <label style="display: block; margin-bottom: 0.5rem;">Last Name</label>
    <input type="text" name="last_name" value="{{ customer.last_name if customer else '' }}" required style="width: 100%; padding: 0.5rem; border: 1px solid var(--border-color); border-radius: 0.25rem;">
</div>
<div class="form-group" style="margin-bottom: 1rem;">
    <label style="display: block; margin-bottom: 0.5rem;">Company</label>
    <input type="text" name="company" value="{{ customer.company if customer else '' }}" style="width: 100%; padding: 0.5rem; border: 1px solid var(--border-color); border-radius: 0.25rem;">
</div>
<div class="form-group" style="margin-bottom: 1rem;">
    <label style="display: block; margin-bottom: 0.5rem;">Email</label>
    <input type="email" name="email" value="{{ customer.email if customer else '' }}" style="width: 100%; padding: 0.5rem; border: 1px solid var(--border-color); border-radius: 0.25rem;">
</div>
<div class="form-group" style="margin-bottom: 1rem;">
    <label style="display: block; margin-bottom: 0.5rem;">Status</label>
    <select name="status" style="width: 100%; padding: 0.5rem; border: 1px solid var(--border-color); border-radius: 0.25rem;">
        <option value="Active" {% if customer and customer.status == 'Active' %}selected{% endif %}>Active</option>
        <option value="Inactive" {% if customer and customer.status == 'Inactive' %}selected{% endif %}>Inactive</option>
        <option value="Lead" {% if customer and customer.status == 'Lead' %}selected{% endif %}>Lead</option>
    </select>
</div>
'''

with open('templates/customers/create.html', 'w', encoding='utf-8') as f:
    f.write('''{% extends "base/base.html" %}
{% block title %}Add Customer - SimpleCRM{% endblock %}
{% block content %}
<div class="card">
    <h1>Add New Customer</h1>
    <form method="POST" action="{{ url_for('customers.create_customer') }}" style="max-width: 600px; margin-top: 1.5rem;">
        ''' + form_template_content + '''
        <button type="submit" class="btn btn-primary">Create Customer</button>
        <a href="{{ url_for('customers.list_customers') }}" class="btn" style="background: var(--border-color);">Cancel</a>
    </form>
</div>
{% endblock %}
''')

with open('templates/customers/edit.html', 'w', encoding='utf-8') as f:
    f.write('''{% extends "base/base.html" %}
{% block title %}Edit Customer - SimpleCRM{% endblock %}
{% block content %}
<div class="card">
    <h1>Edit Customer: {{ customer.first_name }} {{ customer.last_name }}</h1>
    <form method="POST" action="{{ url_for('customers.edit_customer', record_id=customer.id) }}" style="max-width: 600px; margin-top: 1.5rem;">
        ''' + form_template_content + '''
        <button type="submit" class="btn btn-primary">Save Changes</button>
        <a href="{{ url_for('customers.view_customer', record_id=customer.id) }}" class="btn" style="background: var(--border-color);">Cancel</a>
    </form>
</div>
{% endblock %}
''')

with open('templates/customers/view.html', 'w', encoding='utf-8') as f:
    f.write('''{% extends "base/base.html" %}
{% block title %}{{ customer.first_name }} {{ customer.last_name }} - SimpleCRM{% endblock %}
{% block content %}
<div class="card" style="display: flex; justify-content: space-between; align-items: flex-start;">
    <div>
        <h1>{{ customer.first_name }} {{ customer.last_name }}</h1>
        <p style="color: var(--text-muted); font-size: 1.1rem; margin-top: 0.5rem;">
            {{ customer.company }} &bull; {{ customer.status }}
        </p>
    </div>
    <div style="display: flex; gap: 0.5rem;">
        <a href="{{ url_for('customers.edit_customer', record_id=customer.id) }}" class="btn btn-primary">Edit</a>
        <form method="POST" action="{{ url_for('customers.delete_customer', record_id=customer.id) }}" onsubmit="return confirm('Are you sure you want to delete this customer?');">
            <button type="submit" class="btn" style="background: var(--danger-color); color: white;">Delete</button>
        </form>
    </div>
</div>

<div class="card">
    <h2>Contact Information</h2>
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1rem;">
        <div>
            <strong>Email:</strong><br>
            <a href="mailto:{{ customer.email }}">{{ customer.email }}</a>
        </div>
        <div>
            <strong>Phone:</strong><br>
            {{ customer.phone if customer.phone else 'N/A' }}
        </div>
    </div>
</div>
{% endblock %}
''')

# --- UPDATE APP INIT ---
with open('app/__init__.py', 'r', encoding='utf-8') as f:
    content = f.read()

if 'app.register_blueprint(customers_bp)' not in content:
    content = content.replace(
        'return app',
        "    from app.customers import bp as customers_bp\n    app.register_blueprint(customers_bp)\n\n    return app"
    )
    with open('app/__init__.py', 'w', encoding='utf-8') as f:
        f.write(content)

# --- UPDATE BASE TEMPLATE NAV ---
with open('templates/base/base.html', 'r', encoding='utf-8') as f:
    base_html = f.read()

if 'href="/customers"' not in base_html:
    nav_link = '<li><a href="{{ url_for(\'customers.list_customers\') }}">Customers</a></li>\n                    <!-- Future links will go here -->'
    base_html = base_html.replace('<!-- Future links will go here -->', nav_link)
    with open('templates/base/base.html', 'w', encoding='utf-8') as f:
        f.write(base_html)
