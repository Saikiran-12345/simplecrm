from flask import render_template, request, current_app
from app.search import bp
from app.auth.utils import login_required
from app.utils.storage import BaseStorage

def get_storage(name):
    return BaseStorage(current_app.config['DATA_DIR'], name)

@bp.route('/search')
@login_required
def global_search():
    query = request.args.get('q', '').lower()
    results = []
    
    if query:
        # Search Customers
        for c in get_storage('customers').get_all_records():
            if query in c.get('first_name', '').lower() or query in c.get('last_name', '').lower() or query in c.get('company', '').lower():
                results.append({'type': 'Customer', 'title': f"{c.get('first_name')} {c.get('last_name')}", 'desc': c.get('company'), 'link': f"/customers/{c.get('id')}"})
                
        # Search Leads
        for l in get_storage('leads').get_all_records():
            if query in l.get('name', '').lower() or query in l.get('company', '').lower():
                results.append({'type': 'Lead', 'title': l.get('name'), 'desc': l.get('company'), 'link': '/leads'})
                
        # Search Opportunities
        for o in get_storage('opportunities').get_all_records():
            if query in o.get('title', '').lower():
                results.append({'type': 'Opportunity', 'title': o.get('title'), 'desc': f"Stage: {o.get('stage')}", 'link': '/opportunities'})

    return render_template('search/results.html', query=query, results=results)
