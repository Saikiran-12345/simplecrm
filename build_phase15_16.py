import os

# Create directories
os.makedirs('app/reports', exist_ok=True)
os.makedirs('templates/reports', exist_ok=True)
os.makedirs('app/analytics', exist_ok=True)
os.makedirs('templates/analytics', exist_ok=True)

# --- REPORTS BLUEPRINT ---
with open('app/reports/__init__.py', 'w', encoding='utf-8') as f:
    f.write('''from flask import Blueprint
bp = Blueprint('reports', __name__)
from app.reports import routes
''')

with open('app/reports/routes.py', 'w', encoding='utf-8') as f:
    f.write('''from flask import render_template, request, Response, current_app
from app.reports import bp
from app.auth.utils import login_required, role_required
from app.utils.storage import BaseStorage
import pandas as pd
from io import StringIO
from datetime import datetime

def get_storage(name):
    return BaseStorage(current_app.config['DATA_DIR'], name)

@bp.route('/reports')
@login_required
def index():
    return render_template('reports/index.html')

@bp.route('/reports/export/<module>')
@login_required
@role_required('Admin', 'Manager')
def export_csv(module):
    allowed_modules = ['customers', 'leads', 'opportunities', 'sales', 'invoices', 'tasks', 'contacts']
    if module not in allowed_modules:
        return "Invalid module for export", 400
        
    storage = get_storage(module)
    data = storage.get_all_records()
    
    if not data:
        # Return empty CSV
        return Response("", mimetype="text/csv", headers={"Content-disposition": f"attachment; filename={module}.csv"})
        
    # Flatten dicts if necessary (e.g., sales items), but pandas handles basic dicts well
    df = pd.DataFrame(data)
    
    # Drop complex lists like 'items' if exporting sales
    if 'items' in df.columns:
        df = df.drop(columns=['items'])
        
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    
    filename = f"{module}_export_{datetime.today().strftime('%Y%m%d')}.csv"
    
    return Response(
        csv_buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename={filename}"}
    )
''')

with open('templates/reports/index.html', 'w', encoding='utf-8') as f:
    f.write('''{% extends "base/base.html" %}
{% block title %}Reports - SimpleCRM{% endblock %}
{% block content %}
<div class="card">
    <h1>Data Export & Reports</h1>
    <p style="color: var(--text-muted); margin-bottom: 1.5rem;">Download your CRM data in CSV format for external reporting or backups.</p>
    
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem;">
        
        <div class="card" style="border: 1px solid var(--border-color); box-shadow: none;">
            <h3>Customer Data</h3>
            <p style="margin-bottom: 1rem; color: var(--text-muted);">Export all active and inactive customers.</p>
            <a href="{{ url_for('reports.export_csv', module='customers') }}" class="btn btn-primary">Export CSV</a>
        </div>
        
        <div class="card" style="border: 1px solid var(--border-color); box-shadow: none;">
            <h3>Sales & Revenue</h3>
            <p style="margin-bottom: 1rem; color: var(--text-muted);">Export all finalized sales records.</p>
            <a href="{{ url_for('reports.export_csv', module='sales') }}" class="btn btn-primary">Export CSV</a>
        </div>
        
        <div class="card" style="border: 1px solid var(--border-color); box-shadow: none;">
            <h3>Leads Pipeline</h3>
            <p style="margin-bottom: 1rem; color: var(--text-muted);">Export all leads and their conversion statuses.</p>
            <a href="{{ url_for('reports.export_csv', module='leads') }}" class="btn btn-primary">Export CSV</a>
        </div>
        
        <div class="card" style="border: 1px solid var(--border-color); box-shadow: none;">
            <h3>Opportunities</h3>
            <p style="margin-bottom: 1rem; color: var(--text-muted);">Export opportunity forecasting and stages.</p>
            <a href="{{ url_for('reports.export_csv', module='opportunities') }}" class="btn btn-primary">Export CSV</a>
        </div>
        
        <div class="card" style="border: 1px solid var(--border-color); box-shadow: none;">
            <h3>Invoices</h3>
            <p style="margin-bottom: 1rem; color: var(--text-muted);">Export billing records.</p>
            <a href="{{ url_for('reports.export_csv', module='invoices') }}" class="btn btn-primary">Export CSV</a>
        </div>
        
    </div>
</div>
{% endblock %}
''')

# --- ANALYTICS BLUEPRINT ---
with open('app/analytics/__init__.py', 'w', encoding='utf-8') as f:
    f.write('''from flask import Blueprint
bp = Blueprint('analytics', __name__)
from app.analytics import routes
''')

with open('app/analytics/routes.py', 'w', encoding='utf-8') as f:
    f.write('''from flask import render_template, current_app
from app.analytics import bp
from app.auth.utils import login_required
from app.utils.storage import BaseStorage
from collections import defaultdict
import datetime

def get_storage(name):
    return BaseStorage(current_app.config['DATA_DIR'], name)

@bp.route('/analytics')
@login_required
def index():
    # 1. Lead Conversion Rate
    leads = get_storage('leads').get_all_records()
    total_leads = len(leads)
    converted_leads = len([l for l in leads if l.get('status') == 'Converted'])
    conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0.0
    
    # 2. Opportunity Win/Loss Ratio
    opps = get_storage('opportunities').get_all_records()
    won_opps = len([o for o in opps if o.get('stage') == 'Won'])
    lost_opps = len([o for o in opps if o.get('stage') == 'Lost'])
    resolved_opps = won_opps + lost_opps
    win_rate = (won_opps / resolved_opps * 100) if resolved_opps > 0 else 0.0
    
    # 3. Sales by Month
    sales = get_storage('sales').get_all_records()
    sales_by_month = defaultdict(float)
    for s in sales:
        date_str = s.get('sales_date', '')
        if len(date_str) >= 7:
            month = date_str[:7] # YYYY-MM
            sales_by_month[month] += float(s.get('total', 0))
            
    # Sort months chronologically
    sorted_months = sorted(sales_by_month.keys())
    monthly_sales = [{'month': m, 'total': sales_by_month[m]} for m in sorted_months][-6:] # Last 6 months
    
    # Find max for bar chart scaling
    max_sales = max([m['total'] for m in monthly_sales]) if monthly_sales else 1.0
    if max_sales == 0: max_sales = 1.0
    
    return render_template('analytics/index.html', 
                           conversion_rate=conversion_rate, 
                           total_leads=total_leads,
                           win_rate=win_rate,
                           won_opps=won_opps,
                           lost_opps=lost_opps,
                           monthly_sales=monthly_sales,
                           max_sales=max_sales)
''')

with open('templates/analytics/index.html', 'w', encoding='utf-8') as f:
    f.write('''{% extends "base/base.html" %}
{% block title %}Analytics - SimpleCRM{% endblock %}
{% block content %}
<div class="card">
    <h1>Advanced Analytics</h1>
    <p style="color: var(--text-muted);">Key performance indicators and sales trends.</p>
</div>

<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-bottom: 1.5rem;">
    
    <!-- Lead Conversion -->
    <div class="card">
        <h2>Lead Conversion Rate</h2>
        <div style="display: flex; align-items: center; justify-content: center; height: 150px; flex-direction: column;">
            <div style="font-size: 3rem; font-weight: bold; color: var(--primary-color);">{{ "%.1f"|format(conversion_rate) }}%</div>
            <p style="color: var(--text-muted);">Based on {{ total_leads }} total leads</p>
        </div>
        <div style="width: 100%; height: 12px; border-radius: 6px; background: #e2e8f0; overflow: hidden; margin-top: 1rem;">
            <div style="width: {{ conversion_rate }}%; height: 100%; background: var(--primary-color);"></div>
        </div>
    </div>
    
    <!-- Win/Loss Ratio -->
    <div class="card">
        <h2>Opportunity Win Rate</h2>
        <div style="display: flex; align-items: center; justify-content: center; height: 150px; flex-direction: column;">
            <div style="font-size: 3rem; font-weight: bold; color: var(--success-color);">{{ "%.1f"|format(win_rate) }}%</div>
            <p style="color: var(--text-muted);">{{ won_opps }} Won / {{ lost_opps }} Lost</p>
        </div>
        <div style="width: 100%; height: 12px; border-radius: 6px; background: var(--danger-color); overflow: hidden; margin-top: 1rem; display: flex;">
            <div style="width: {{ win_rate }}%; height: 100%; background: var(--success-color);"></div>
        </div>
    </div>
    
</div>

<!-- Sales by Month Bar Chart -->
<div class="card">
    <h2>Sales Trend (Last 6 Months)</h2>
    <div style="display: flex; align-items: flex-end; justify-content: space-around; height: 250px; padding-top: 2rem; border-bottom: 1px solid var(--border-color);">
        {% for item in monthly_sales %}
        <div style="display: flex; flex-direction: column; align-items: center; width: 40px;">
            <div style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 0.25rem;">${{ "%.0f"|format(item.total) }}</div>
            <div style="width: 100%; background: var(--primary-color); border-radius: 4px 4px 0 0; min-height: 2px; height: {{ (item.total / max_sales) * 200 }}px; transition: height 0.5s ease;"></div>
            <div style="margin-top: 0.5rem; font-size: 0.85rem; font-weight: 500;">{{ item.month[-2:] }}</div>
        </div>
        {% else %}
        <p style="color: var(--text-muted); align-self: center;">No sales data available yet.</p>
        {% endfor %}
    </div>
</div>
{% endblock %}
''')


# --- UPDATE APP INIT ---
content = """import os
from flask import Flask, session
from config.settings import config
from app.utils.logger import setup_logger

def create_app(config_name='default'):
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config.from_object(config[config_name])
    setup_logger(app)
    os.makedirs(app.config['DATA_DIR'], exist_ok=True)
    
    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    from app.dashboard import bp as dashboard_bp
    app.register_blueprint(dashboard_bp)
    from app.users import bp as users_bp
    app.register_blueprint(users_bp)
    from app.customers import bp as customers_bp
    app.register_blueprint(customers_bp)
    from app.contacts import bp as contacts_bp
    app.register_blueprint(contacts_bp)
    from app.leads import bp as leads_bp
    app.register_blueprint(leads_bp)
    from app.opportunities import bp as opportunities_bp
    app.register_blueprint(opportunities_bp)
    from app.tasks import bp as tasks_bp
    app.register_blueprint(tasks_bp)
    from app.followups import bp as followups_bp
    app.register_blueprint(followups_bp)
    from app.products import bp as products_bp
    app.register_blueprint(products_bp)
    from app.sales import bp as sales_bp
    app.register_blueprint(sales_bp)
    from app.invoices import bp as invoices_bp
    app.register_blueprint(invoices_bp)
    from app.payments import bp as payments_bp
    app.register_blueprint(payments_bp)
    from app.notes import bp as notes_bp
    app.register_blueprint(notes_bp)
    from app.reports import bp as reports_bp
    app.register_blueprint(reports_bp)
    from app.analytics import bp as analytics_bp
    app.register_blueprint(analytics_bp)

    return app
"""
with open('app/__init__.py', 'w', encoding='utf-8') as f:
    f.write(content)

# --- UPDATE BASE TEMPLATE NAV ---
with open('templates/base/base.html', 'r', encoding='utf-8') as f:
    base_html = f.read()

if 'href="/reports"' not in base_html:
    nav_link = '''<li><a href="{{ url_for('reports.index') }}">Reports</a></li>
                    <li><a href="{{ url_for('analytics.index') }}">Analytics</a></li>
                    <!-- Future links will go here -->'''
    base_html = base_html.replace('<!-- Future links will go here -->', nav_link)
    with open('templates/base/base.html', 'w', encoding='utf-8') as f:
        f.write(base_html)
