"""
Workflow Automation UI Routes
"""
from flask import render_template, request, redirect, url_for, flash, current_app
from app.automations import bp
from app.auth.utils import login_required, role_required
from app.utils.storage import BaseStorage

@bp.route('/automations', methods=['GET'])
@login_required
@role_required('Admin')
def index():
    storage = BaseStorage(current_app.config['DATA_DIR'], 'automations')
    workflows = storage.get_all_records()
    return render_template('automations/index.html', workflows=workflows)

@bp.route('/automations/create', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def create():
    if request.method == 'POST':
        # Simplify for brevity, in a massive app this would parse dynamic arrays
        data = {
            'name': request.form.get('name'),
            'module': request.form.get('module'),
            'event_type': request.form.get('event_type'),
            'status': 'Active',
            'conditions': [{
                'field': request.form.get('cond_field'),
                'operator': request.form.get('cond_operator'),
                'value': request.form.get('cond_value')
            }],
            'actions': [{
                'type': request.form.get('action_type'),
                'payload': {'title': 'Auto Task', 'user': 'admin', 'message': 'Action fired!'}
            }]
        }
        storage = BaseStorage(current_app.config['DATA_DIR'], 'automations')
        storage.create_record(data)
        flash('Workflow created!', 'success')
        return redirect(url_for('automations.index'))
    return render_template('automations/create.html')
