from flask import render_template, redirect, url_for, flash, request, session
from werkzeug.security import check_password_hash
from app.auth import bp
from app.utils.storage import BaseStorage
from flask import current_app

def get_user_storage():
    return BaseStorage(current_app.config['DATA_DIR'], 'users')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        storage = get_user_storage()
        users = storage.search_records(username=username)
        
        if len(users) == 1:
            user = users[0]
            if user.get('status') != 'Active':
                flash('Account is inactive.', 'danger')
            elif check_password_hash(user['password_hash'], password):
                session.clear()
                session['user_id'] = user['id']
                session['user_role'] = user['role']
                session['username'] = user['username']
                flash('Successfully logged in.', 'success')
                return redirect(url_for('dashboard.index'))
            else:
                # Track failed login here eventually
                flash('Invalid username or password.', 'danger')
        else:
            flash('Invalid username or password.', 'danger')
            
    return render_template('auth/login.html')

@bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
