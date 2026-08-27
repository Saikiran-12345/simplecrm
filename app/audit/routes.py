from flask import render_template, current_app
from app.audit import bp
from app.auth.utils import login_required, role_required
from app.utils.storage import BaseStorage

@bp.route('/audit')
@login_required
@role_required('Admin')
def index():
    storage = BaseStorage(current_app.config['DATA_DIR'], 'audit')
    # Get last 100 audit logs (reverse chronological)
    logs = storage.get_all_records()
    logs.reverse()
    return render_template('audit/index.html', logs=logs[:100])
