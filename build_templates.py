import os

# --- TEMPLATES ---
with open('templates/auth/login.html', 'w', encoding='utf-8') as f:
    f.write('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - SimpleCRM</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
    <style>
        .login-container {
            max-width: 400px;
            margin: 100px auto;
            padding: 2rem;
        }
        .form-group {
            margin-bottom: 1rem;
        }
        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 500;
        }
        .form-control {
            width: 100%;
            padding: 0.5rem;
            border: 1px solid var(--border-color);
            border-radius: 0.25rem;
        }
        .btn-block {
            display: block;
            width: 100%;
            text-align: center;
        }
    </style>
</head>
<body style="background-color: var(--bg-color);">
    <div class="login-container card">
        <h2 style="text-align: center; margin-bottom: 1.5rem;">SimpleCRM Login</h2>
        
        <div class="flash-messages">
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ category }}">
                            {{ message }}
                        </div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
        </div>

        <form method="POST" action="{{ url_for('auth.login') }}">
            <div class="form-group">
                <label for="username">Username</label>
                <input type="text" id="username" name="username" class="form-control" required autofocus>
            </div>
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" class="form-control" required>
            </div>
            <button type="submit" class="btn btn-primary btn-block">Log In</button>
        </form>
    </div>
</body>
</html>
''')

with open('templates/dashboard/index.html', 'w', encoding='utf-8') as f:
    f.write('''{% extends "base/base.html" %}
{% block title %}Dashboard - SimpleCRM{% endblock %}
{% block content %}
<div class="card">
    <h1>Dashboard</h1>
    <p>Welcome back, {{ session.get('username') }}! You are logged in as {{ session.get('user_role') }}.</p>
</div>
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
    <div class="card" style="text-align: center;">
        <h3>Total Customers</h3>
        <p style="font-size: 2rem; font-weight: bold; color: var(--primary-color);">0</p>
    </div>
    <div class="card" style="text-align: center;">
        <h3>Active Leads</h3>
        <p style="font-size: 2rem; font-weight: bold; color: var(--warning-color);">0</p>
    </div>
    <div class="card" style="text-align: center;">
        <h3>Open Tasks</h3>
        <p style="font-size: 2rem; font-weight: bold; color: var(--danger-color);">0</p>
    </div>
</div>
{% endblock %}
''')

with open('templates/users/list.html', 'w', encoding='utf-8') as f:
    f.write('''{% extends "base/base.html" %}
{% block title %}Users - SimpleCRM{% endblock %}
{% block content %}
<div class="card" style="display: flex; justify-content: space-between; align-items: center;">
    <h1>User Management</h1>
    <a href="#" class="btn btn-primary">Add User</a>
</div>
<div class="card">
    <table style="width: 100%; border-collapse: collapse;">
        <thead>
            <tr style="border-bottom: 2px solid var(--border-color); text-align: left;">
                <th style="padding: 0.75rem;">Username</th>
                <th style="padding: 0.75rem;">Role</th>
                <th style="padding: 0.75rem;">Status</th>
                <th style="padding: 0.75rem;">Actions</th>
            </tr>
        </thead>
        <tbody>
            {% for user in users %}
            <tr style="border-bottom: 1px solid var(--border-color);">
                <td style="padding: 0.75rem;">{{ user.username }}</td>
                <td style="padding: 0.75rem;">{{ user.role }}</td>
                <td style="padding: 0.75rem;">
                    <span style="padding: 0.25rem 0.5rem; border-radius: 9999px; font-size: 0.875rem; background-color: {% if user.status == 'Active' %}#dcfce7; color: #166534;{% else %}#fee2e2; color: #991b1b;{% endif %}">
                        {{ user.status }}
                    </span>
                </td>
                <td style="padding: 0.75rem;">
                    <a href="#" style="color: var(--primary-color); text-decoration: none; margin-right: 0.5rem;">Edit</a>
                </td>
            </tr>
            {% else %}
            <tr>
                <td colspan="4" style="padding: 1rem; text-align: center; color: var(--text-muted);">No users found.</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}
''')

# --- UPDATE APP INIT ---
app_init = '''import os
from flask import Flask, session
from config.settings import config
from app.utils.logger import setup_logger

def create_app(config_name='default'):
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Set up logger
    setup_logger(app)
    
    # Ensure data directory exists
    os.makedirs(app.config['DATA_DIR'], exist_ok=True)
    
    # Register blueprints
    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)
    
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from app.dashboard import bp as dashboard_bp
    app.register_blueprint(dashboard_bp)
    
    from app.users import bp as users_bp
    app.register_blueprint(users_bp)
    
    return app
'''
with open('app/__init__.py', 'w', encoding='utf-8') as f:
    f.write(app_init)
