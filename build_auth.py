import os

# --- AUTH BLUEPRINT ---
with open('app/auth/__init__.py', 'w', encoding='utf-8') as f:
    f.write('''from flask import Blueprint
bp = Blueprint('auth', __name__)
from app.auth import routes
''')

with open('app/auth/utils.py', 'w', encoding='utf-8') as f:
    f.write('''from functools import wraps
from flask import session, redirect, url_for, flash

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login'))
            if session.get('user_role') not in roles:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('dashboard.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator
''')

with open('app/auth/routes.py', 'w', encoding='utf-8') as f:
    f.write('''from flask import render_template, redirect, url_for, flash, request, session
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
''')

# --- DASHBOARD BLUEPRINT (Default view after login) ---
with open('app/dashboard/__init__.py', 'w', encoding='utf-8') as f:
    f.write('''from flask import Blueprint
bp = Blueprint('dashboard', __name__)
from app.dashboard import routes
''')

with open('app/dashboard/routes.py', 'w', encoding='utf-8') as f:
    f.write('''from flask import render_template
from app.dashboard import bp
from app.auth.utils import login_required

@bp.route('/')
@login_required
def index():
    return render_template('dashboard/index.html')
''')

# --- USERS BLUEPRINT ---
with open('app/users/__init__.py', 'w', encoding='utf-8') as f:
    f.write('''from flask import Blueprint
bp = Blueprint('users', __name__)
from app.users import routes
''')

with open('app/users/routes.py', 'w', encoding='utf-8') as f:
    f.write('''from flask import render_template, request, redirect, url_for, flash
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
''')
