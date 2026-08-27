# Finish writing templates for Tasks and Followups
task_form = """
<div class="form-group"><label>Description</label><input type="text" name="description" value="{{ task.description if task else '' }}" required class="form-control"></div>
<div class="form-group"><label>Due Date</label><input type="date" name="due_date" value="{{ task.due_date if task else '' }}" class="form-control"></div>
<div class="form-group"><label>Priority</label><select name="priority" class="form-control">
    <option value="Low" {% if task and task.priority == 'Low' %}selected{% endif %}>Low</option>
    <option value="Medium" {% if task and task.priority == 'Medium' %}selected{% endif %}>Medium</option>
    <option value="High" {% if task and task.priority == 'High' %}selected{% endif %}>High</option>
</select></div>
<div class="form-group"><label>Status</label><select name="status" class="form-control">
    <option value="Pending" {% if task and task.status == 'Pending' %}selected{% endif %}>Pending</option>
    <option value="In Progress" {% if task and task.status == 'In Progress' %}selected{% endif %}>In Progress</option>
    <option value="Completed" {% if task and task.status == 'Completed' %}selected{% endif %}>Completed</option>
    <option value="Cancelled" {% if task and task.status == 'Cancelled' %}selected{% endif %}>Cancelled</option>
</select></div>
"""

with open('templates/tasks/create.html', 'w', encoding='utf-8') as f:
    f.write('{% extends "base/base.html" %}{% block content %}<div class="card"><h1>Add Task</h1><form method="POST">' + task_form + '<button class="btn btn-primary">Save</button></form></div>{% endblock %}')

with open('templates/tasks/edit.html', 'w', encoding='utf-8') as f:
    f.write('{% extends "base/base.html" %}{% block content %}<div class="card"><h1>Edit Task</h1><form method="POST">' + task_form + '<button class="btn btn-primary">Save</button></form></div>{% endblock %}')

followup_form = """
<div class="form-group"><label>Notes</label><textarea name="notes" class="form-control" required>{{ followup.notes if followup else '' }}</textarea></div>
<div class="form-group"><label>Due Date</label><input type="date" name="due_date" value="{{ followup.due_date if followup else '' }}" class="form-control"></div>
<div class="form-group"><label>Priority</label><select name="priority" class="form-control">
    <option value="Low" {% if followup and followup.priority == 'Low' %}selected{% endif %}>Low</option>
    <option value="Medium" {% if followup and followup.priority == 'Medium' %}selected{% endif %}>Medium</option>
    <option value="High" {% if followup and followup.priority == 'High' %}selected{% endif %}>High</option>
</select></div>
<div class="form-group"><label>Status</label><select name="status" class="form-control">
    <option value="Pending" {% if followup and followup.status == 'Pending' %}selected{% endif %}>Pending</option>
    <option value="In Progress" {% if followup and followup.status == 'In Progress' %}selected{% endif %}>In Progress</option>
    <option value="Completed" {% if followup and followup.status == 'Completed' %}selected{% endif %}>Completed</option>
    <option value="Cancelled" {% if followup and followup.status == 'Cancelled' %}selected{% endif %}>Cancelled</option>
</select></div>
"""

with open('templates/followups/list.html', 'w', encoding='utf-8') as f:
    f.write('{% extends "base/base.html" %}{% block content %}<div class="card"><h1>Follow-ups</h1><a href="{{ url_for(\'followups.create_followup\') }}" class="btn btn-primary">Add Follow-up</a></div><div class="card"><ul>{% for f in followups %}<li><a href="{{ url_for(\'followups.edit_followup\', record_id=f.id) }}">{{ f.notes }}</a> ({{ f.status }})</li>{% endfor %}</ul></div>{% endblock %}')

with open('templates/followups/create.html', 'w', encoding='utf-8') as f:
    f.write('{% extends "base/base.html" %}{% block content %}<div class="card"><h1>Add Follow-up</h1><form method="POST">' + followup_form + '<button class="btn btn-primary">Save</button></form></div>{% endblock %}')

with open('templates/followups/edit.html', 'w', encoding='utf-8') as f:
    f.write('{% extends "base/base.html" %}{% block content %}<div class="card"><h1>Edit Follow-up</h1><form method="POST">' + followup_form + '<button class="btn btn-primary">Save</button></form></div>{% endblock %}')
