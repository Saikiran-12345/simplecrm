from flask import render_template, request, redirect, url_for, flash, current_app
from app.employees import bp
from app.auth.utils import login_required, role_required
from app.utils.storage import BaseStorage

def get_storage():
    return BaseStorage(current_app.config['DATA_DIR'], 'employees')

@bp.route('/employees')
@login_required
@role_required('Admin', 'Manager')
def list_employees():
    storage = get_storage()
    search_query = request.args.get('q', '').lower()
    all_employees = storage.get_all_records()
    if search_query:
        employees = [e for e in all_employees if search_query in e.get('name', '').lower() or search_query in e.get('department', '').lower()]
    else:
        employees = all_employees
    return render_template('employees/list.html', employees=employees, search_query=search_query)

@bp.route('/employees/create', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def create_employee():
    if request.method == 'POST':
        data = {
            'name': request.form.get('name'),
            'title': request.form.get('title'),
            'department': request.form.get('department'),
            'email': request.form.get('email'),
            'phone': request.form.get('phone'),
            'hire_date': request.form.get('hire_date'),
            'salary': request.form.get('salary', '0'),
            'performance_rating': request.form.get('performance_rating', 'N/A')
        }
        storage = get_storage()
        storage.create_record(data)
        flash('Employee created successfully.', 'success')
        return redirect(url_for('employees.list_employees'))
    return render_template('employees/create.html')
