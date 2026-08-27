content = """from flask import render_template, request, redirect, url_for, flash, current_app
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
        
        # Phase 23: Data Validation Hook
        from app.utils.validators import is_valid_email, validate_required
        is_valid, msg = validate_required(data, ['first_name'])
        if not is_valid:
            flash(msg, 'danger')
            return redirect(url_for('customers.create_customer'))
            
        if data.get('email') and not is_valid_email(data.get('email')):
            flash('Invalid email format provided.', 'danger')
            return redirect(url_for('customers.create_customer'))
            
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
"""
with open('app/customers/routes.py', 'w', encoding='utf-8') as f:
    f.write(content)
