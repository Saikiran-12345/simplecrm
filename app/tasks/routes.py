from flask import render_template, request, redirect, url_for, flash, current_app
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
