from flask import render_template, request, redirect, url_for, flash, current_app
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
