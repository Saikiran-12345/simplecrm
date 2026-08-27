"""
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
