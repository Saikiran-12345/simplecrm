from flask import render_template, request, redirect, url_for, flash, current_app
from app.rbac import bp
from app.auth.utils import login_required, role_required
from app.utils.storage import BaseStorage

@bp.route('/rbac')
@login_required
@role_required('Admin')
def list_roles():
    storage = BaseStorage(current_app.config['DATA_DIR'], 'users')
    users = storage.get_all_records()
    return render_template('rbac/list.html', users=users)

@bp.route('/rbac/update', methods=['POST'])
@login_required
@role_required('Admin')
def update_role():
    user_id = request.form.get('user_id')
    new_role = request.form.get('role')
    if user_id and new_role in ['Admin', 'Manager', 'User']:
        storage = BaseStorage(current_app.config['DATA_DIR'], 'users')
        storage.update_record(user_id, {'role': new_role})
        flash('User role updated.', 'success')
    return redirect(url_for('rbac.list_roles'))
