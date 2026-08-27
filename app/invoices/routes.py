from flask import render_template, request, redirect, url_for, flash, current_app
from app.invoices import bp
from app.auth.utils import login_required
from app.utils.storage import BaseStorage
from datetime import datetime

def get_storage(name):
    return BaseStorage(current_app.config['DATA_DIR'], name)

@bp.route('/invoices')
@login_required
def list_invoices():
    storage = get_storage('invoices')
    search_query = request.args.get('q', '').lower()
    all_invoices = storage.get_all_records()
    
    c_storage = get_storage('customers')
    for inv in all_invoices:
        cust = c_storage.get_record(inv.get('customer_id', ''))
        inv['customer_name'] = f"{cust.get('first_name')} {cust.get('last_name')}" if cust else "Unknown"
            
    if search_query:
        invoices = [i for i in all_invoices if search_query in i.get('invoice_number', '').lower() or search_query in i.get('customer_name', '').lower()]
    else:
        invoices = all_invoices
        
    return render_template('invoices/list.html', invoices=invoices, search_query=search_query)

@bp.route('/invoices/create', methods=['GET', 'POST'])
@login_required
def create_invoice():
    if request.method == 'POST':
        product_ids = request.form.getlist('product_id[]')
        quantities = request.form.getlist('quantity[]')
        
        p_storage = get_storage('products')
        items = []
        subtotal = 0.0
        
        for p_id, qty_str in zip(product_ids, quantities):
            if not p_id: continue
            qty = float(qty_str) if qty_str else 0.0
            prod = p_storage.get_record(p_id)
            if prod:
                price = float(prod.get('price', 0))
                items.append({'product_name': prod.get('name'), 'quantity': qty, 'price': price, 'line_total': price * qty})
                subtotal += (price * qty)

        discount = float(request.form.get('discount', 0))
        tax_rate = float(request.form.get('tax', 0))
        tax_amount = (subtotal - discount) * (tax_rate / 100.0)
        total = subtotal - discount + tax_amount
        
        # Generate Invoice Number INV-YYYYMMDD-XXXX
        import random
        inv_number = f"INV-{datetime.today().strftime('%Y%m%d')}-{random.randint(1000,9999)}"
        
        data = {
            'invoice_number': inv_number,
            'customer_id': request.form.get('customer_id'),
            'invoice_date': request.form.get('invoice_date'),
            'due_date': request.form.get('due_date'),
            'status': request.form.get('status', 'Draft'),
            'items': items,
            'subtotal': subtotal,
            'discount': discount,
            'tax_rate': tax_rate,
            'tax_amount': tax_amount,
            'total': total
        }
        storage = get_storage('invoices')
        inv_id = storage.create_record(data)
        flash('Invoice created successfully.', 'success')
        return redirect(url_for('invoices.view_invoice', record_id=inv_id))
        
    customers = get_storage('customers').get_all_records()
    products = [p for p in get_storage('products').get_all_records() if p.get('status') == 'Active']
    return render_template('invoices/create.html', customers=customers, products=products)

@bp.route('/invoices/<record_id>')
@login_required
def view_invoice(record_id):
    storage = get_storage('invoices')
    invoice = storage.get_record(record_id)
    if not invoice:
        flash('Invoice not found.', 'danger')
        return redirect(url_for('invoices.list_invoices'))
        
    cust = get_storage('customers').get_record(invoice.get('customer_id'))
    return render_template('invoices/view.html', invoice=invoice, customer=cust)
