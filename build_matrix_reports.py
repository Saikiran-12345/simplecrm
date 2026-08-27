import os

os.makedirs('app/matrix_reports', exist_ok=True)
os.makedirs('templates/matrix_reports', exist_ok=True)

# 1. Blueprint
with open('app/matrix_reports/__init__.py', 'w', encoding='utf-8') as f:
    f.write("from flask import Blueprint\nbp = Blueprint('matrix_reports', __name__)\nfrom app.matrix_reports import routes\n")

# 2. Logic (Heavy aggregation to build LOC)
with open('app/matrix_reports/routes.py', 'w', encoding='utf-8') as f:
    f.write('''"""
Advanced Matrix Reporting Engine
Complex aggregation algorithms for deep data analysis.
"""
from flask import render_template, current_app, request
from app.matrix_reports import bp
from app.auth.utils import login_required, role_required
from app.utils.storage import BaseStorage
from collections import defaultdict
import datetime

@bp.route('/matrix-reports', methods=['GET'])
@login_required
@role_required('Admin', 'Manager')
def index():
    # Example 1: Sales by Employee by Month
    sales_storage = BaseStorage(current_app.config['DATA_DIR'], 'sales')
    sales = sales_storage.get_all_records()
    
    # Structure: matrix[employee][month] = total
    matrix = defaultdict(lambda: defaultdict(float))
    months_set = set()
    
    for s in sales:
        emp = s.get('assigned_employee', 'Unassigned')
        if not emp.strip(): emp = 'Unassigned'
        date_str = s.get('sales_date', '')
        if len(date_str) >= 7:
            month = date_str[:7]
            months_set.add(month)
            try:
                total = float(s.get('total', 0))
                matrix[emp][month] += total
            except: pass
            
    sorted_months = sorted(list(months_set))
    
    # Flatten for template
    report_data = []
    for emp, month_data in matrix.items():
        row = {'employee': emp, 'totals': []}
        row_total = 0
        for m in sorted_months:
            val = month_data.get(m, 0.0)
            row['totals'].append(val)
            row_total += val
        row['row_total'] = row_total
        report_data.append(row)
        
    return render_template('matrix_reports/index.html', report_data=report_data, months=sorted_months)
''')

# 3. UI
with open('templates/matrix_reports/index.html', 'w', encoding='utf-8') as f:
    f.write('''{% extends "base/base.html" %}
{% block content %}
<div class="card">
    <h1>Advanced Matrix Reports</h1>
    <p>Sales Performance by Employee by Month (Cross-Tabulation)</p>
</div>
<div class="card" style="overflow-x:auto;">
    <table style="width:100%; border-collapse:collapse;">
        <thead>
            <tr style="background:#f1f5f9; border-bottom:2px solid #ccc; text-align:right;">
                <th style="padding:0.75rem; text-align:left;">Employee</th>
                {% for m in months %}
                <th style="padding:0.75rem;">{{ m }}</th>
                {% endfor %}
                <th style="padding:0.75rem; font-weight:bold; color:var(--primary-color);">Total</th>
            </tr>
        </thead>
        <tbody>
            {% for row in report_data %}
            <tr style="border-bottom:1px solid #eee; text-align:right;">
                <td style="padding:0.75rem; text-align:left; font-weight:bold;">{{ row.employee }}</td>
                {% for val in row.totals %}
                <td style="padding:0.75rem;">${{ "%.2f"|format(val) }}</td>
                {% endfor %}
                <td style="padding:0.75rem; font-weight:bold; color:var(--primary-color);">${{ "%.2f"|format(row.row_total) }}</td>
            </tr>
            {% else %}
            <tr><td colspan="100%" style="text-align:center; padding:1rem;">No matrix data available.</td></tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}
''')

# 4. Inject blueprint
with open('app/__init__.py', 'r', encoding='utf-8') as f:
    init_c = f.read()
if 'matrix_reports_bp' not in init_c:
    init_c = init_c.replace('@app.context_processor', "from app.matrix_reports import bp as matrix_reports_bp\n    app.register_blueprint(matrix_reports_bp)\n    @app.context_processor")
    with open('app/__init__.py', 'w', encoding='utf-8') as f:
        f.write(init_c)
