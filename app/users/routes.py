from flask import render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash
from app.users import bp
from app.auth.utils import login_required, role_required
from app.utils.storage import BaseStorage
from flask import current_app

def get_user_storage():
    return BaseStorage(current_app.config['DATA_DIR'], 'users')

@bp.route('/users')
@login_required
@role_required('Admin')
def list_users():
    storage = get_user_storage()
    users = storage.get_all_records()
    return render_template('users/list.html', users=users)
