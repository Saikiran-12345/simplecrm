from flask import render_template, request, redirect, url_for, flash, current_app, session
from app.notes import bp
from app.auth.utils import login_required
from app.utils.storage import BaseStorage

def get_storage(name):
    return BaseStorage(current_app.config['DATA_DIR'], name)

@bp.route('/notes')
@login_required
def list_notes():
    storage = get_storage('notes')
    search_query = request.args.get('q', '').lower()
    all_notes = storage.get_all_records()
    
    if search_query:
        notes = [n for n in all_notes if search_query in n.get('content', '').lower() or search_query in n.get('entity_type', '').lower()]
    else:
        notes = all_notes
        
    return render_template('notes/list.html', notes=notes, search_query=search_query)

@bp.route('/notes/create', methods=['POST'])
@login_required
def create_note():
    entity_type = request.form.get('entity_type')
    entity_id = request.form.get('entity_id')
    content = request.form.get('content')
    return_url = request.form.get('return_url', url_for('notes.list_notes'))
    
    if not content:
        flash('Note content cannot be empty.', 'danger')
        return redirect(return_url)
        
    storage = get_storage('notes')
    storage.create_record({
        'entity_type': entity_type,
        'entity_id': entity_id,
        'content': content,
        'author': session.get('username')
    })
    
    flash('Note added successfully.', 'success')
    return redirect(return_url)

@bp.route('/notes/<record_id>/delete', methods=['POST'])
@login_required
def delete_note(record_id):
    storage = get_storage('notes')
    return_url = request.form.get('return_url', url_for('notes.list_notes'))
    if storage.delete_record(record_id):
        flash('Note deleted.', 'success')
    else:
        flash('Note not found.', 'danger')
    return redirect(return_url)
