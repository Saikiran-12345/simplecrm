from flask import render_template, request, redirect, url_for, flash, current_app
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
