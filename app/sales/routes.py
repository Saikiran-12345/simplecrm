from flask import render_template, request, redirect, url_for, flash, current_app, session
from app.sales import bp
from app.auth.utils import login_required
from app.utils.storage import BaseStorage
from datetime import datetime

def get_storage(name):
    return BaseStorage(current_app.config['DATA_DIR'], name)

@bp.route('/sales')
@login_required
def list_sales():
    storage = get_storage('sales')
    search_query = request.args.get('q', '').lower()
    all_sales = storage.get_all_records()
    
    c_storage = get_storage('customers')
    
    for s in all_sales:
        cust = c_storage.get_record(s.get('customer_id', ''))
        s['customer_name'] = f"{cust.get('first_name')} {cust.get('last_name')}" if cust else "Unknown"
            
    if search_query:
        sales = [s for s in all_sales if search_query in s.get('customer_name', '').lower() or search_query in s.get('status', '').lower()]
    else:
        sales = all_sales
        
    return render_template('sales/list.html', sales=sales, search_query=search_query)

@bp.route('/sales/create', methods=['GET', 'POST'])
@login_required
def create_sale():
    if request.method == 'POST':
        product_ids = request.form.getlist('product_id[]')
        quantities = request.form.getlist('quantity[]')
        
        if not product_ids:
            flash('At least one product must be selected.', 'danger')
            return redirect(url_for('sales.create_sale'))

        p_storage = get_storage('products')
        
        items = []
        subtotal = 0.0
        
        for p_id, qty_str in zip(product_ids, quantities):
            if not p_id:
                continue
            qty = float(qty_str) if qty_str else 0.0
            prod = p_storage.get_record(p_id)
            if prod:
                price = float(prod.get('price', 0))
                line_total = price * qty
                subtotal += line_total
                items.append({
                    'product_id': p_id,
                    'product_name': prod.get('name'),
                    'quantity': qty,
                    'price': price,
                    'line_total': line_total
                })
                
                # Update inventory
                current_qty = float(prod.get('quantity', 0))
                new_qty = max(0, current_qty - qty)
                p_storage.update_record(p_id, {'quantity': str(new_qty)})

        discount = float(request.form.get('discount', 0))
        tax_rate = float(request.form.get('tax', 0)) # Percentage
        
        tax_amount = (subtotal - discount) * (tax_rate / 100.0)
        total = subtotal - discount + tax_amount
        
        data = {
            'customer_id': request.form.get('customer_id'),
            'sales_date': request.form.get('sales_date', datetime.today().strftime('%Y-%m-%d')),
            'status': request.form.get('status', 'Completed'),
            'assigned_employee': session.get('username', ''),
            'items': items,
            'subtotal': subtotal,
            'discount': discount,
            'tax_rate': tax_rate,
            'tax_amount': tax_amount,
            'total': total
        }
        storage = get_storage('sales')
        sale_id = storage.create_record(data)
        flash('Sale created successfully.', 'success')
        return redirect(url_for('sales.view_sale', record_id=sale_id))
        
    customers = get_storage('customers').get_all_records()
    products = [p for p in get_storage('products').get_all_records() if p.get('status') == 'Active']
    return render_template('sales/create.html', customers=customers, products=products)

@bp.route('/sales/<record_id>')
@login_required
def view_sale(record_id):
    storage = get_storage('sales')
    sale = storage.get_record(record_id)
    if not sale:
        flash('Sale not found.', 'danger')
        return redirect(url_for('sales.list_sales'))
        
    cust = get_storage('customers').get_record(sale.get('customer_id'))
    customer_name = f"{cust.get('first_name')} {cust.get('last_name')}" if cust else "Unknown"
    
    return render_template('sales/view.html', sale=sale, customer_name=customer_name)
