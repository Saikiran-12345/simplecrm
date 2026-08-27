from flask import render_template, request, redirect, url_for, flash, current_app
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
