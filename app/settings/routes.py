from flask import render_template, request, redirect, url_for, flash, current_app
from app.settings import bp
from app.auth.utils import login_required, role_required
from app.utils.storage import BaseStorage

@bp.route('/settings', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def index():
    storage = BaseStorage(current_app.config['DATA_DIR'], 'settings')
    settings_records = storage.get_all_records()
    
    # Simple key-value structure
    settings = {}
    for r in settings_records:
        settings[r.get('key')] = r.get('value')
        
    if request.method == 'POST':
        keys = ['company_name', 'default_currency', 'timezone', 'theme']
        for k in keys:
            val = request.form.get(k)
            # Find existing
            existing = [r for r in settings_records if r.get('key') == k]
            if existing:
                storage.update_record(existing[0]['id'], {'value': val})
            else:
                storage.create_record({'key': k, 'value': val})
        flash('Settings updated successfully.', 'success')
        return redirect(url_for('settings.index'))
        
    return render_template('settings/index.html', settings=settings)
