from flask import render_template, request, Response, current_app
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
