"""
Dynamic Custom Fields Module
Allows Admins to define new fields for any module without altering database schema.
"""
from flask import render_template, request, redirect, url_for, flash, current_app
from app.custom_fields import bp
from app.auth.utils import login_required, role_required
from app.utils.storage import BaseStorage

@bp.route('/custom-fields', methods=['GET'])
@login_required
@role_required('Admin')
def index():
    storage = BaseStorage(current_app.config['DATA_DIR'], 'custom_fields')
    fields = storage.get_all_records()
    return render_template('custom_fields/index.html', fields=fields)

@bp.route('/custom-fields/create', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def create():
    if request.method == 'POST':
        data = {
            'module': request.form.get('module'),
            'field_name': request.form.get('field_name').replace(' ', '_').lower(),
            'field_label': request.form.get('field_label'),
            'field_type': request.form.get('field_type'),
            'is_required': request.form.get('is_required') == 'on'
        }
        storage = BaseStorage(current_app.config['DATA_DIR'], 'custom_fields')
        storage.create_record(data)
        flash('Custom Field created!', 'success')
        return redirect(url_for('custom_fields.index'))
    return render_template('custom_fields/create.html')
