from flask import render_template, current_app
from app.dashboard import bp
from app.auth.utils import login_required
from app.utils.storage import BaseStorage
from datetime import datetime

def get_storage(name):
    return BaseStorage(current_app.config['DATA_DIR'], name)

@bp.route('/')
@login_required
def index():
    # Gather metrics
    today = datetime.today().strftime('%Y-%m-%d')
    
    customers = get_storage('customers').get_all_records()
    total_customers = len(customers)
    new_customers = len([c for c in customers if c.get('created_at', '').startswith(today)])
    
    leads = get_storage('leads').get_all_records()
    total_leads = len(leads)
    qualified_leads = len([l for l in leads if l.get('status') == 'Qualified'])
    
    opportunities = get_storage('opportunities').get_all_records()
    open_opps = len([o for o in opportunities if o.get('stage') not in ['Won', 'Lost']])
    won_opps = len([o for o in opportunities if o.get('stage') == 'Won'])
    
    sales = get_storage('sales').get_all_records()
    total_sales = sum([float(s.get('total', 0)) for s in sales])
    
    invoices = get_storage('invoices').get_all_records()
    pending_invoices = len([i for i in invoices if i.get('status') == 'Sent'])
    paid_invoices = len([i for i in invoices if i.get('status') == 'Paid'])
    overdue_invoices = len([i for i in invoices if i.get('status') not in ['Paid', 'Cancelled'] and i.get('due_date', '') < today])
    
    tasks = get_storage('tasks').get_all_records()
    pending_tasks = len([t for t in tasks if t.get('status') in ['Pending', 'In Progress']])
    completed_tasks = len([t for t in tasks if t.get('status') == 'Completed'])
    
    followups = get_storage('followups').get_all_records()
    due_followups = len([f for f in followups if f.get('due_date', '') == today and f.get('status') != 'Completed'])
    overdue_followups = len([f for f in followups if f.get('due_date', '') < today and f.get('status') != 'Completed'])
    
    metrics = {
        'total_customers': total_customers, 'new_customers': new_customers,
        'total_leads': total_leads, 'qualified_leads': qualified_leads,
        'open_opps': open_opps, 'won_opps': won_opps,
        'total_sales': total_sales,
        'pending_invoices': pending_invoices, 'paid_invoices': paid_invoices, 'overdue_invoices': overdue_invoices,
        'pending_tasks': pending_tasks, 'completed_tasks': completed_tasks,
        'due_followups': due_followups, 'overdue_followups': overdue_followups
    }
    return render_template('dashboard/index.html', metrics=metrics)
