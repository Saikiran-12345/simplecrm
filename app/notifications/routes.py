from flask import render_template, redirect, url_for, request, current_app, session
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
