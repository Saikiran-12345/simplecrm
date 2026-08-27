import os
import re

os.makedirs('app/search', exist_ok=True)
os.makedirs('templates/search', exist_ok=True)
os.makedirs('app/notifications', exist_ok=True)
os.makedirs('templates/notifications', exist_ok=True)

# ==========================================
# PHASE 23: VALIDATORS
# ==========================================
with open('app/utils/validators.py', 'w', encoding='utf-8') as f:
    f.write('''import re

def is_valid_email(email):
    if not email: return True # Optional field support
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(pattern, email) is not None

def is_valid_phone(phone):
    if not phone: return True
    # Strip common characters
    cleaned = re.sub(r'[\s\-\(\)\+]', '', phone)
    return cleaned.isdigit() and len(cleaned) >= 7

def validate_required(data_dict, required_keys):
    missing = [k for k in required_keys if not data_dict.get(k) or not str(data_dict.get(k)).strip()]
    if missing:
        return False, f"Missing required fields: {', '.join(missing)}"
    return True, ""
''')

# Update Customer Creation to use Validators
with open('app/customers/routes.py', 'r', encoding='utf-8') as f:
    c_routes = f.read()

validation_injection = '''
        # Phase 23: Data Validation Hook
        from app.utils.validators import is_valid_email, validate_required
        is_valid, msg = validate_required(data, ['first_name'])
        if not is_valid:
            flash(msg, 'danger')
            return redirect(url_for('customers.create_customer'))
            
        if data.get('email') and not is_valid_email(data.get('email')):
            flash('Invalid email format provided.', 'danger')
            return redirect(url_for('customers.create_customer'))
'''

if 'Data Validation Hook' not in c_routes:
    # Insert right after `data = {...}` block
    c_routes = c_routes.replace(
        "storage = get_storage()",
        validation_injection + "\n        storage = get_storage()"
    )
    with open('app/customers/routes.py', 'w', encoding='utf-8') as f:
        f.write(c_routes)


# ==========================================
# PHASE 21: GLOBAL SEARCH
# ==========================================
with open('app/search/__init__.py', 'w', encoding='utf-8') as f:
    f.write("from flask import Blueprint\nbp = Blueprint('search', __name__)\nfrom app.search import routes\n")

with open('app/search/routes.py', 'w', encoding='utf-8') as f:
    f.write('''from flask import render_template, request, current_app
from app.search import bp
from app.auth.utils import login_required
from app.utils.storage import BaseStorage

def get_storage(name):
    return BaseStorage(current_app.config['DATA_DIR'], name)

@bp.route('/search')
@login_required
def global_search():
    query = request.args.get('q', '').lower()
    results = []
    
    if query:
        # Search Customers
        for c in get_storage('customers').get_all_records():
            if query in c.get('first_name', '').lower() or query in c.get('last_name', '').lower() or query in c.get('company', '').lower():
                results.append({'type': 'Customer', 'title': f"{c.get('first_name')} {c.get('last_name')}", 'desc': c.get('company'), 'link': f"/customers/{c.get('id')}"})
                
        # Search Leads
        for l in get_storage('leads').get_all_records():
            if query in l.get('name', '').lower() or query in l.get('company', '').lower():
                results.append({'type': 'Lead', 'title': l.get('name'), 'desc': l.get('company'), 'link': '/leads'})
                
        # Search Opportunities
        for o in get_storage('opportunities').get_all_records():
            if query in o.get('title', '').lower():
                results.append({'type': 'Opportunity', 'title': o.get('title'), 'desc': f"Stage: {o.get('stage')}", 'link': '/opportunities'})

    return render_template('search/results.html', query=query, results=results)
''')

with open('templates/search/results.html', 'w', encoding='utf-8') as f:
    f.write('''{% extends "base/base.html" %}
{% block title %}Search Results - SimpleCRM{% endblock %}
{% block content %}
<div class="card">
    <h1>Global Search Results</h1>
    <p>Searching for: <strong>"{{ query }}"</strong></p>
</div>
<div class="card">
    {% if results %}
        <ul style="list-style-type: none; padding: 0;">
        {% for r in results %}
            <li style="padding: 1rem; border-bottom: 1px solid var(--border-color);">
                <span style="display:inline-block; padding:0.25rem 0.5rem; background:#e2e8f0; border-radius:4px; font-size:0.75rem; margin-right:1rem;">{{ r.type }}</span>
                <a href="{{ r.link }}" style="font-weight: bold; color: var(--primary-color); font-size:1.1rem; text-decoration:none;">{{ r.title }}</a>
                <span style="color: var(--text-muted); margin-left: 1rem;">{{ r.desc }}</span>
            </li>
        {% endfor %}
        </ul>
    {% else %}
        <p style="padding: 1rem; text-align: center; color: var(--text-muted);">No results found.</p>
    {% endif %}
</div>
{% endblock %}
''')


# ==========================================
# PHASE 22: NOTIFICATIONS
# ==========================================
with open('app/notifications/__init__.py', 'w', encoding='utf-8') as f:
    f.write("from flask import Blueprint\nbp = Blueprint('notifications', __name__)\nfrom app.notifications import routes\n")

with open('app/notifications/routes.py', 'w', encoding='utf-8') as f:
    f.write('''from flask import render_template, redirect, url_for, request, current_app, session
from app.notifications import bp
from app.auth.utils import login_required
from app.utils.storage import BaseStorage

@bp.route('/notifications')
@login_required
def index():
    storage = BaseStorage(current_app.config['DATA_DIR'], 'notifications')
    username = session.get('username')
    my_notes = [n for n in storage.get_all_records() if n.get('user') == username]
    my_notes.reverse() # Newest first
    return render_template('notifications/index.html', notifications=my_notes)

@bp.route('/notifications/<record_id>/read', methods=['POST'])
@login_required
def mark_read(record_id):
    storage = BaseStorage(current_app.config['DATA_DIR'], 'notifications')
    storage.update_record(record_id, {'is_read': True})
    return redirect(url_for('notifications.index'))

@bp.route('/notifications/mark_all', methods=['POST'])
@login_required
def mark_all_read():
    storage = BaseStorage(current_app.config['DATA_DIR'], 'notifications')
    username = session.get('username')
    for n in storage.get_all_records():
        if n.get('user') == username and not n.get('is_read'):
            storage.update_record(n.get('id'), {'is_read': True})
    return redirect(url_for('notifications.index'))
''')

with open('templates/notifications/index.html', 'w', encoding='utf-8') as f:
    f.write('''{% extends "base/base.html" %}
{% block title %}Notifications - SimpleCRM{% endblock %}
{% block content %}
<div class="card" style="display:flex; justify-content:space-between; align-items:center;">
    <h1>My Notifications</h1>
    <form method="POST" action="{{ url_for('notifications.mark_all_read') }}">
        <button class="btn" style="background:var(--border-color);">Mark All as Read</button>
    </form>
</div>
<div class="card">
    <ul style="list-style:none; padding:0;">
        {% for n in notifications %}
        <li style="padding: 1rem; border-bottom: 1px solid var(--border-color); display:flex; justify-content:space-between; align-items:center; background: {% if not n.is_read %}#f0fdf4{% else %}transparent{% endif %};">
            <div>
                <strong style="color:var(--text-color);">{{ n.message }}</strong>
                <div style="font-size:0.8rem; color:var(--text-muted);">{{ n.created_at[:16] }}</div>
            </div>
            {% if not n.is_read %}
            <form method="POST" action="{{ url_for('notifications.mark_read', record_id=n.id) }}">
                <button class="btn btn-primary" style="padding:0.25rem 0.5rem; font-size:0.8rem;">Mark Read</button>
            </form>
            {% else %}
            <span style="font-size:0.8rem; color:var(--text-muted);">Read</span>
            {% endif %}
        </li>
        {% else %}
        <p style="text-align:center; color:var(--text-muted); padding:1rem;">No notifications yet.</p>
        {% endfor %}
    </ul>
</div>
{% endblock %}
''')

# INJECT UNREAD COUNT INTO CONTEXT PROCESSOR
with open('app/__init__.py', 'r', encoding='utf-8') as f:
    init_content = f.read()

cp_injection = """
        settings = {r.get('key'): r.get('value') for r in storage.get_all_records()}
        
        unread_count = 0
        if 'username' in session:
            n_storage = BaseStorage(app.config['DATA_DIR'], 'notifications')
            unread_count = len([n for n in n_storage.get_all_records() if n.get('user') == session['username'] and not n.get('is_read')])
            
        return dict(global_settings=settings, unread_notifications=unread_count)
"""
if 'unread_notifications' not in init_content:
    init_content = init_content.replace(
        "settings = {r.get('key'): r.get('value') for r in storage.get_all_records()}\n        return dict(global_settings=settings)",
        cp_injection
    )
    
bp_registrations2 = """
    from app.search import bp as search_bp
    app.register_blueprint(search_bp)
    from app.notifications import bp as notif_bp
    app.register_blueprint(notif_bp)
    
    @app.context_processor
"""
init_content = init_content.replace('@app.context_processor', bp_registrations2)
with open('app/__init__.py', 'w', encoding='utf-8') as f:
    f.write(init_content)


# ==========================================
# PHASE 24: UI POLISH
# ==========================================
with open('static/css/style.css', 'w', encoding='utf-8') as f:
    f.write('''
:root {
    --primary-color: #2563eb;
    --primary-hover: #1d4ed8;
    --secondary-color: #475569;
    --bg-color: #f8fafc;
    --card-bg: #ffffff;
    --text-color: #1e293b;
    --text-muted: #64748b;
    --border-color: #e2e8f0;
    --success-color: #16a34a;
    --danger-color: #dc2626;
    --warning-color: #f59e0b;
    --header-height: 60px;
    --sidebar-width: 250px;
}

* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: var(--bg-color); color: var(--text-color); line-height: 1.6; }

.app-container { display: flex; min-height: 100vh; }

/* Sidebar */
.sidebar { width: var(--sidebar-width); background-color: var(--card-bg); border-right: 1px solid var(--border-color); display: flex; flex-direction: column; z-index: 10;}
.sidebar-header { padding: 1.5rem; border-bottom: 1px solid var(--border-color); }
.sidebar-header h2 { color: var(--primary-color); font-size: 1.5rem; letter-spacing: 0.5px;}
.sidebar-nav { padding: 1rem 0; flex-grow: 1; overflow-y: auto; }
.sidebar-nav ul { list-style: none; }
.sidebar-nav a { display: block; padding: 0.75rem 1.5rem; color: var(--secondary-color); text-decoration: none; transition: all 0.2s; font-weight: 500;}
.sidebar-nav a:hover { background-color: #eff6ff; color: var(--primary-color); border-left: 3px solid var(--primary-color); }

/* Main Content Area */
.main-content { flex-grow: 1; display: flex; flex-direction: column; }

/* Header Navbar */
.top-header { height: var(--header-height); background: var(--card-bg); border-bottom: 1px solid var(--border-color); display: flex; align-items: center; justify-content: space-between; padding: 0 2rem; }
.search-bar { display: flex; align-items: center; }
.search-bar input { padding: 0.5rem 1rem; border: 1px solid var(--border-color); border-radius: 20px; width: 300px; outline: none; transition: border-color 0.2s;}
.search-bar input:focus { border-color: var(--primary-color); }
.header-actions { display: flex; align-items: center; gap: 1.5rem; }
.header-actions a { text-decoration: none; color: var(--text-color); font-weight: 500; }
.badge { background: var(--danger-color); color: white; border-radius: 50%; padding: 0.15rem 0.5rem; font-size: 0.75rem; font-weight: bold; margin-left: 0.25rem;}

/* Main Body */
.content-wrapper { padding: 2rem; max-width: 1200px; margin: 0 auto; width: 100%; }

/* Cards & Components */
.card { background-color: var(--card-bg); border-radius: 0.5rem; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03); padding: 1.5rem; margin-bottom: 1.5rem; transition: transform 0.2s; }
h1, h2, h3 { margin-bottom: 1rem; color: var(--text-color); }

/* Buttons */
.btn { display: inline-block; padding: 0.5rem 1rem; border-radius: 0.25rem; text-decoration: none; cursor: pointer; font-size: 0.875rem; font-weight: 500; border: none; transition: background-color 0.2s, transform 0.1s; }
.btn:active { transform: scale(0.98); }
.btn-primary { background-color: var(--primary-color); color: white; }
.btn-primary:hover { background-color: var(--primary-hover); }

/* Forms & Tables */
.form-group label { font-weight: 500; margin-bottom: 0.25rem; display: block; font-size: 0.9rem;}
.form-control, input[type="text"], input[type="email"], input[type="password"], input[type="number"], input[type="date"], select, textarea { 
    width: 100%; padding: 0.6rem; border: 1px solid var(--border-color); border-radius: 0.25rem; outline: none; font-family: inherit; transition: border-color 0.2s; 
}
.form-control:focus, input:focus, select:focus, textarea:focus { border-color: var(--primary-color); box-shadow: 0 0 0 2px rgba(37,99,235,0.1); }
table tbody tr:hover { background-color: #f8fafc; }
.alert { padding: 1rem; margin-bottom: 1rem; border-radius: 0.25rem; font-weight: 500;}
.alert-success { background-color: #dcfce7; color: #166534; }
.alert-danger { background-color: #fee2e2; color: #991b1b; }
''')

# Update Base HTML Structure to support Top Header
with open('templates/base/base.html', 'w', encoding='utf-8') as f:
    f.write('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}{{ global_settings.get('company_name', 'SimpleCRM') }}{% endblock %}</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    <div class="app-container">
        <!-- Sidebar -->
        <aside class="sidebar" id="sidebar">
            <div class="sidebar-header">
                <h2>{{ global_settings.get('company_name', 'SimpleCRM') }}</h2>
            </div>
            <nav class="sidebar-nav">
                <ul>
                    <li><a href="{{ url_for('dashboard.index') }}">Dashboard</a></li>
                    <li><a href="{{ url_for('customers.list_customers') }}">Customers</a></li>
                    <li><a href="{{ url_for('contacts.list_contacts') }}">Contacts</a></li>
                    <li><a href="{{ url_for('leads.list_leads') }}">Leads</a></li>
                    <li><a href="{{ url_for('opportunities.list_opportunities') }}">Opportunities</a></li>
                    <li><a href="{{ url_for('products.list_products') }}">Products</a></li>
                    <li><a href="{{ url_for('sales.list_sales') }}">Sales</a></li>
                    <li><a href="{{ url_for('invoices.list_invoices') }}">Invoices</a></li>
                    <li><a href="{{ url_for('payments.list_payments') }}">Payments</a></li>
                    <li><a href="{{ url_for('tasks.list_tasks') }}">Tasks</a></li>
                    <li><a href="{{ url_for('followups.list_followups') }}">Follow-ups</a></li>
                    <li><a href="{{ url_for('notes.list_notes') }}">Notes</a></li>
                    <li><a href="{{ url_for('reports.index') }}">Reports</a></li>
                    <li><a href="{{ url_for('analytics.index') }}">Analytics</a></li>
                    
                    {% if session.get('user_role') == 'Admin' %}
                    <li style="margin-top:1.5rem; padding-left:1.5rem; font-size:0.75rem; text-transform:uppercase; color:var(--text-muted); font-weight:bold;">Administration</li>
                    <li><a href="{{ url_for('employees.list_employees') }}">Employees</a></li>
                    <li><a href="{{ url_for('rbac.list_roles') }}">User Roles</a></li>
                    <li><a href="{{ url_for('audit.index') }}">Audit Logs</a></li>
                    <li><a href="{{ url_for('settings.index') }}">Settings</a></li>
                    {% endif %}
                </ul>
            </nav>
        </aside>

        <!-- Main Content -->
        <main class="main-content">
            <!-- Top Navbar -->
            <header class="top-header">
                <form class="search-bar" action="{{ url_for('search.global_search') }}" method="GET">
                    <input type="text" name="q" placeholder="Global Search (Customers, Leads, Opps)...">
                </form>
                
                <div class="header-actions">
                    <a href="{{ url_for('notifications.index') }}">
                        Alerts 
                        {% if unread_notifications and unread_notifications > 0 %}
                        <span class="badge">{{ unread_notifications }}</span>
                        {% endif %}
                    </a>
                    
                    {% if session.get('user_id') %}
                    <span>{{ session.get('username') }} ({{ session.get('user_role') }})</span>
                    <a href="{{ url_for('auth.logout') }}" style="color:var(--danger-color);">Logout</a>
                    {% else %}
                    <a href="{{ url_for('auth.login') }}">Login</a>
                    {% endif %}
                </div>
            </header>

            <div class="content-wrapper">
                {% with messages = get_flashed_messages(with_categories=true) %}
                    {% if messages %}
                        {% for category, message in messages %}
                            <div class="alert alert-{{ category }}">{{ message }}</div>
                        {% endfor %}
                    {% endif %}
                {% endwith %}
                
                {% block content %}{% endblock %}
            </div>
        </main>
    </div>
    <script src="{{ url_for('static', filename='js/main.js') }}"></script>
    {% block scripts %}{% endblock %}
</body>
</html>
''')
