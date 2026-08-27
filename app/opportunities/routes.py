from flask import render_template, request, redirect, url_for, flash, current_app
from app.opportunities import bp
from app.auth.utils import login_required
from app.utils.storage import BaseStorage

def get_storage(name):
    return BaseStorage(current_app.config['DATA_DIR'], name)

@bp.route('/opportunities')
@login_required
def list_opportunities():
    storage = get_storage('opportunities')
    cust_storage = get_storage('customers')
    lead_storage = get_storage('leads')
    
    search_query = request.args.get('q', '').lower()
    
    all_opps = storage.get_all_records()
    
    # Map associations
    for opp in all_opps:
        if opp.get('customer_id'):
            c = cust_storage.get_record(opp['customer_id'])
            opp['associated_name'] = f"Customer: {c.get('first_name')} {c.get('last_name')}" if c else "Unknown Customer"
        elif opp.get('lead_id'):
            l = lead_storage.get_record(opp['lead_id'])
            opp['associated_name'] = f"Lead: {l.get('name')}" if l else "Unknown Lead"
        else:
            opp['associated_name'] = "None"
            
        # Calculate expected value (Value * Probability / 100)
        try:
            val = float(opp.get('value', 0))
            prob = float(opp.get('probability', 0))
            opp['weighted_value'] = val * (prob / 100)
        except ValueError:
            opp['weighted_value'] = 0.0

    if search_query:
        opps = [o for o in all_opps if search_query in o.get('title', '').lower() or 
                search_query in o.get('associated_name', '').lower()]
    else:
        opps = all_opps
        
    return render_template('opportunities/list.html', opportunities=opps, search_query=search_query)

@bp.route('/opportunities/create', methods=['GET', 'POST'])
@login_required
def create_opportunity():
    customers = get_storage('customers').get_all_records()
    leads = get_storage('leads').get_all_records()
    
    if request.method == 'POST':
        data = {
            'title': request.form.get('title'),
            'description': request.form.get('description'),
            'value': request.form.get('value', '0'),
            'probability': request.form.get('probability', '0'),
            'stage': request.form.get('stage', 'New'),
            'expected_close_date': request.form.get('expected_close_date'),
            'assigned_employee': request.form.get('assigned_employee', ''),
            'customer_id': request.form.get('customer_id'),
            'lead_id': request.form.get('lead_id')
        }
        storage = get_storage('opportunities')
        storage.create_record(data)
        flash('Opportunity created successfully.', 'success')
        return redirect(url_for('opportunities.list_opportunities'))
        
    return render_template('opportunities/create.html', customers=customers, leads=leads)

@bp.route('/opportunities/<record_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_opportunity(record_id):
    storage = get_storage('opportunities')
    opp = storage.get_record(record_id)
    if not opp:
        flash('Opportunity not found.', 'danger')
        return redirect(url_for('opportunities.list_opportunities'))
        
    customers = get_storage('customers').get_all_records()
    leads = get_storage('leads').get_all_records()
        
    if request.method == 'POST':
        data = {
            'title': request.form.get('title'),
            'description': request.form.get('description'),
            'value': request.form.get('value'),
            'probability': request.form.get('probability'),
            'stage': request.form.get('stage'),
            'expected_close_date': request.form.get('expected_close_date'),
            'assigned_employee': request.form.get('assigned_employee'),
            'customer_id': request.form.get('customer_id'),
            'lead_id': request.form.get('lead_id')
        }
        storage.update_record(record_id, data)
        flash('Opportunity updated successfully.', 'success')
        return redirect(url_for('opportunities.list_opportunities'))
        
    return render_template('opportunities/edit.html', opportunity=opp, customers=customers, leads=leads)

@bp.route('/opportunities/<record_id>/delete', methods=['POST'])
@login_required
def delete_opportunity(record_id):
    storage = get_storage('opportunities')
    if storage.delete_record(record_id):
        flash('Opportunity deleted successfully.', 'success')
    else:
        flash('Opportunity not found.', 'danger')
    return redirect(url_for('opportunities.list_opportunities'))
