from flask import render_template, request, redirect, url_for, flash, current_app
from app.payments import bp
from app.auth.utils import login_required
from app.utils.storage import BaseStorage

def get_storage(name):
    return BaseStorage(current_app.config['DATA_DIR'], name)

@bp.route('/payments')
@login_required
def list_payments():
    storage = get_storage('payments')
    search_query = request.args.get('q', '').lower()
    all_payments = storage.get_all_records()
    
    i_storage = get_storage('invoices')
    c_storage = get_storage('customers')
    
    for p in all_payments:
        inv = i_storage.get_record(p.get('invoice_id', ''))
        cust = c_storage.get_record(p.get('customer_id', ''))
        p['invoice_number'] = inv.get('invoice_number') if inv else "N/A"
        p['customer_name'] = f"{cust.get('first_name')} {cust.get('last_name')}" if cust else "N/A"
            
    if search_query:
        payments = [p for p in all_payments if search_query in p.get('invoice_number', '').lower()]
    else:
        payments = all_payments
        
    return render_template('payments/list.html', payments=payments, search_query=search_query)

@bp.route('/payments/create', methods=['GET', 'POST'])
@login_required
def create_payment():
    if request.method == 'POST':
        data = {
            'invoice_id': request.form.get('invoice_id'),
            'customer_id': request.form.get('customer_id'),
            'amount': float(request.form.get('amount', 0)),
            'payment_date': request.form.get('payment_date'),
            'payment_method': request.form.get('payment_method'),
            'status': request.form.get('status', 'Completed'),
            'notes': request.form.get('notes')
        }
        storage = get_storage('payments')
        storage.create_record(data)
        
        # Update invoice status if Paid
        if data['status'] == 'Completed' and data['invoice_id']:
            i_storage = get_storage('invoices')
            inv = i_storage.get_record(data['invoice_id'])
            if inv:
                # Naive implementation: assuming payment covers full amount
                i_storage.update_record(data['invoice_id'], {'status': 'Paid'})
                
        flash('Payment recorded successfully.', 'success')
        return redirect(url_for('payments.list_payments'))
        
    invoices = get_storage('invoices').get_all_records()
    customers = get_storage('customers').get_all_records()
    return render_template('payments/create.html', invoices=invoices, customers=customers)
