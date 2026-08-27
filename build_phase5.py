import os

os.makedirs('app/contacts', exist_ok=True)
os.makedirs('templates/contacts', exist_ok=True)

with open('app/contacts/__init__.py', 'w', encoding='utf-8') as f:
    f.write('''from flask import Blueprint
bp = Blueprint('contacts', __name__)
from app.contacts import routes
''')

with open('app/contacts/routes.py', 'w', encoding='utf-8') as f:
    f.write('''from flask import render_template, request, redirect, url_for, flash, current_app
from app.contacts import bp
from app.auth.utils import login_required
from app.utils.storage import BaseStorage

def get_contact_storage():
    return BaseStorage(current_app.config['DATA_DIR'], 'contacts')

def get_customer_storage():
    return BaseStorage(current_app.config['DATA_DIR'], 'customers')

@bp.route('/contacts')
@login_required
def list_contacts():
    storage = get_contact_storage()
    customer_storage = get_customer_storage()
    search_query = request.args.get('q', '').lower()
    
    all_contacts = storage.get_all_records()
    if search_query:
        contacts = [c for c in all_contacts if search_query in c.get('first_name', '').lower() or 
                     search_query in c.get('last_name', '').lower() or 
                     search_query in c.get('email', '').lower()]
    else:
        contacts = all_contacts
        
    # Map customer names
    for contact in contacts:
        if contact.get('customer_id'):
            cust = customer_storage.get_record(contact['customer_id'])
            if cust:
                contact['customer_name'] = f"{cust.get('first_name')} {cust.get('last_name')}"
                
    return render_template('contacts/list.html', contacts=contacts, search_query=search_query)

@bp.route('/contacts/create', methods=['GET', 'POST'])
@login_required
def create_contact():
    customer_storage = get_customer_storage()
    customers = customer_storage.get_all_records()
    
    if request.method == 'POST':
        data = {
            'first_name': request.form.get('first_name'),
            'last_name': request.form.get('last_name'),
            'email': request.form.get('email'),
            'phone': request.form.get('phone'),
            'title': request.form.get('title'),
            'customer_id': request.form.get('customer_id'),
            'notes': request.form.get('notes')
        }
        storage = get_contact_storage()
        storage.create_record(data)
        flash('Contact created successfully.', 'success')
        return redirect(url_for('contacts.list_contacts'))
        
    return render_template('contacts/create.html', customers=customers)

@bp.route('/contacts/<record_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_contact(record_id):
    storage = get_contact_storage()
    contact = storage.get_record(record_id)
    if not contact:
        flash('Contact not found.', 'danger')
        return redirect(url_for('contacts.list_contacts'))
        
    customer_storage = get_customer_storage()
    customers = customer_storage.get_all_records()
        
    if request.method == 'POST':
        data = {
            'first_name': request.form.get('first_name'),
            'last_name': request.form.get('last_name'),
            'email': request.form.get('email'),
            'phone': request.form.get('phone'),
            'title': request.form.get('title'),
            'customer_id': request.form.get('customer_id'),
            'notes': request.form.get('notes')
        }
        storage.update_record(record_id, data)
        flash('Contact updated successfully.', 'success')
        return redirect(url_for('contacts.list_contacts'))
        
    return render_template('contacts/edit.html', contact=contact, customers=customers)

@bp.route('/contacts/<record_id>/delete', methods=['POST'])
@login_required
def delete_contact(record_id):
    storage = get_contact_storage()
    if storage.delete_record(record_id):
        flash('Contact deleted successfully.', 'success')
    else:
        flash('Contact not found or could not be deleted.', 'danger')
    return redirect(url_for('contacts.list_contacts'))
''')

# --- TEMPLATES ---
with open('templates/contacts/list.html', 'w', encoding='utf-8') as f:
    f.write('''{% extends "base/base.html" %}
{% block title %}Contacts - SimpleCRM{% endblock %}
{% block content %}
<div class="card" style="display: flex; justify-content: space-between; align-items: center;">
    <h1>Contacts</h1>
    <a href="{{ url_for('contacts.create_contact') }}" class="btn btn-primary">Add Contact</a>
</div>

<div class="card">
    <form method="GET" action="{{ url_for('contacts.list_contacts') }}" style="margin-bottom: 1.5rem; display: flex; gap: 1rem;">
        <input type="text" name="q" value="{{ search_query }}" placeholder="Search contacts..." style="flex-grow: 1; padding: 0.5rem; border: 1px solid var(--border-color); border-radius: 0.25rem;">
        <button type="submit" class="btn btn-primary">Search</button>
        {% if search_query %}
            <a href="{{ url_for('contacts.list_contacts') }}" class="btn" style="background: var(--border-color);">Clear</a>
        {% endif %}
    </form>

    <table style="width: 100%; border-collapse: collapse;">
        <thead>
            <tr style="border-bottom: 2px solid var(--border-color); text-align: left;">
                <th style="padding: 0.75rem;">Name</th>
                <th style="padding: 0.75rem;">Title</th>
                <th style="padding: 0.75rem;">Customer</th>
                <th style="padding: 0.75rem;">Email</th>
                <th style="padding: 0.75rem;">Actions</th>
            </tr>
        </thead>
        <tbody>
            {% for contact in contacts %}
            <tr style="border-bottom: 1px solid var(--border-color);">
                <td style="padding: 0.75rem; font-weight: 500;">{{ contact.first_name }} {{ contact.last_name }}</td>
                <td style="padding: 0.75rem;">{{ contact.title }}</td>
                <td style="padding: 0.75rem;">{{ contact.customer_name or 'N/A' }}</td>
                <td style="padding: 0.75rem;">{{ contact.email }}</td>
                <td style="padding: 0.75rem; display: flex; gap: 0.5rem;">
                    <a href="{{ url_for('contacts.edit_contact', record_id=contact.id) }}" style="color: var(--primary-color); text-decoration: none;">Edit</a>
                    <form method="POST" action="{{ url_for('contacts.delete_contact', record_id=contact.id) }}" onsubmit="return confirm('Delete this contact?');" style="display:inline;">
                        <button type="submit" style="background:none; border:none; color:var(--danger-color); cursor:pointer; text-decoration:underline;">Delete</button>
                    </form>
                </td>
            </tr>
            {% else %}
            <tr>
                <td colspan="5" style="padding: 1rem; text-align: center; color: var(--text-muted);">No contacts found.</td>
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
    <input type="text" name="first_name" value="{{ contact.first_name if contact else '' }}" required style="width: 100%; padding: 0.5rem; border: 1px solid var(--border-color); border-radius: 0.25rem;">
</div>
<div class="form-group" style="margin-bottom: 1rem;">
    <label style="display: block; margin-bottom: 0.5rem;">Last Name</label>
    <input type="text" name="last_name" value="{{ contact.last_name if contact else '' }}" required style="width: 100%; padding: 0.5rem; border: 1px solid var(--border-color); border-radius: 0.25rem;">
</div>
<div class="form-group" style="margin-bottom: 1rem;">
    <label style="display: block; margin-bottom: 0.5rem;">Title/Position</label>
    <input type="text" name="title" value="{{ contact.title if contact else '' }}" style="width: 100%; padding: 0.5rem; border: 1px solid var(--border-color); border-radius: 0.25rem;">
</div>
<div class="form-group" style="margin-bottom: 1rem;">
    <label style="display: block; margin-bottom: 0.5rem;">Associated Customer</label>
    <select name="customer_id" style="width: 100%; padding: 0.5rem; border: 1px solid var(--border-color); border-radius: 0.25rem;">
        <option value="">-- None --</option>
        {% for customer in customers %}
        <option value="{{ customer.id }}" {% if contact and contact.customer_id == customer.id %}selected{% endif %}>
            {{ customer.first_name }} {{ customer.last_name }} ({{ customer.company }})
        </option>
        {% endfor %}
    </select>
</div>
<div class="form-group" style="margin-bottom: 1rem;">
    <label style="display: block; margin-bottom: 0.5rem;">Email</label>
    <input type="email" name="email" value="{{ contact.email if contact else '' }}" style="width: 100%; padding: 0.5rem; border: 1px solid var(--border-color); border-radius: 0.25rem;">
</div>
<div class="form-group" style="margin-bottom: 1rem;">
    <label style="display: block; margin-bottom: 0.5rem;">Phone</label>
    <input type="text" name="phone" value="{{ contact.phone if contact else '' }}" style="width: 100%; padding: 0.5rem; border: 1px solid var(--border-color); border-radius: 0.25rem;">
</div>
<div class="form-group" style="margin-bottom: 1rem;">
    <label style="display: block; margin-bottom: 0.5rem;">Notes</label>
    <textarea name="notes" rows="4" style="width: 100%; padding: 0.5rem; border: 1px solid var(--border-color); border-radius: 0.25rem;">{{ contact.notes if contact else '' }}</textarea>
</div>
'''

with open('templates/contacts/create.html', 'w', encoding='utf-8') as f:
    f.write('''{% extends "base/base.html" %}
{% block title %}Add Contact - SimpleCRM{% endblock %}
{% block content %}
<div class="card">
    <h1>Add New Contact</h1>
    <form method="POST" action="{{ url_for('contacts.create_contact') }}" style="max-width: 600px; margin-top: 1.5rem;">
        ''' + form_template_content + '''
        <button type="submit" class="btn btn-primary">Create Contact</button>
        <a href="{{ url_for('contacts.list_contacts') }}" class="btn" style="background: var(--border-color);">Cancel</a>
    </form>
</div>
{% endblock %}
''')

with open('templates/contacts/edit.html', 'w', encoding='utf-8') as f:
    f.write('''{% extends "base/base.html" %}
{% block title %}Edit Contact - SimpleCRM{% endblock %}
{% block content %}
<div class="card">
    <h1>Edit Contact</h1>
    <form method="POST" action="{{ url_for('contacts.edit_contact', record_id=contact.id) }}" style="max-width: 600px; margin-top: 1.5rem;">
        ''' + form_template_content + '''
        <button type="submit" class="btn btn-primary">Save Changes</button>
        <a href="{{ url_for('contacts.list_contacts') }}" class="btn" style="background: var(--border-color);">Cancel</a>
    </form>
</div>
{% endblock %}
''')

# --- UPDATE APP INIT ---
with open('app/__init__.py', 'r', encoding='utf-8') as f:
    content = f.read()

if 'app.register_blueprint(contacts_bp)' not in content:
    content = content.replace(
        'return app',
        "    from app.contacts import bp as contacts_bp\n    app.register_blueprint(contacts_bp)\n\n    return app"
    )
    with open('app/__init__.py', 'w', encoding='utf-8') as f:
        f.write(content)

# --- UPDATE BASE TEMPLATE NAV ---
with open('templates/base/base.html', 'r', encoding='utf-8') as f:
    base_html = f.read()

if 'href="/contacts"' not in base_html:
    nav_link = '<li><a href="{{ url_for(\'contacts.list_contacts\') }}">Contacts</a></li>\n                    <!-- Future links will go here -->'
    base_html = base_html.replace('<!-- Future links will go here -->', nav_link)
    with open('templates/base/base.html', 'w', encoding='utf-8') as f:
        f.write(base_html)
