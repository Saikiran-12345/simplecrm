import os

os.makedirs('app/invoices', exist_ok=True)
os.makedirs('templates/invoices', exist_ok=True)
os.makedirs('app/payments', exist_ok=True)
os.makedirs('templates/payments', exist_ok=True)

# --- INVOICES BLUEPRINT ---
with open('app/invoices/__init__.py', 'w', encoding='utf-8') as f:
    f.write('''from flask import Blueprint
bp = Blueprint('invoices', __name__)
from app.invoices import routes
''')

with open('app/invoices/routes.py', 'w', encoding='utf-8') as f:
    f.write('''from flask import render_template, request, redirect, url_for, flash, current_app
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
''')

# --- PAYMENTS BLUEPRINT ---
with open('app/payments/__init__.py', 'w', encoding='utf-8') as f:
    f.write('''from flask import Blueprint
bp = Blueprint('payments', __name__)
from app.payments import routes
''')

with open('app/payments/routes.py', 'w', encoding='utf-8') as f:
    f.write('''from flask import render_template, request, redirect, url_for, flash, current_app
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
''')

# --- TEMPLATES ---
with open('templates/invoices/list.html', 'w', encoding='utf-8') as f:
    f.write('''{% extends "base/base.html" %}
{% block title %}Invoices - SimpleCRM{% endblock %}
{% block content %}
<div class="card" style="display: flex; justify-content: space-between; align-items: center;">
    <h1>Invoices</h1>
    <a href="{{ url_for('invoices.create_invoice') }}" class="btn btn-primary">Create Invoice</a>
</div>
<div class="card">
    <table style="width: 100%; border-collapse: collapse;">
        <thead>
            <tr style="border-bottom: 2px solid var(--border-color); text-align: left;">
                <th style="padding: 0.75rem;">Inv #</th>
                <th style="padding: 0.75rem;">Date</th>
                <th style="padding: 0.75rem;">Customer</th>
                <th style="padding: 0.75rem;">Status</th>
                <th style="padding: 0.75rem;">Total</th>
                <th style="padding: 0.75rem;">Actions</th>
            </tr>
        </thead>
        <tbody>
            {% for i in invoices %}
            <tr style="border-bottom: 1px solid var(--border-color);">
                <td style="padding: 0.75rem; font-weight: bold;">{{ i.invoice_number }}</td>
                <td style="padding: 0.75rem;">{{ i.invoice_date }}</td>
                <td style="padding: 0.75rem;">{{ i.customer_name }}</td>
                <td style="padding: 0.75rem;">{{ i.status }}</td>
                <td style="padding: 0.75rem;">${{ "%.2f"|format(i.total) }}</td>
                <td style="padding: 0.75rem;">
                    <a href="{{ url_for('invoices.view_invoice', record_id=i.id) }}" style="color: var(--primary-color);">View</a>
                </td>
            </tr>
            {% else %}
            <tr><td colspan="6" style="padding: 1rem; text-align: center;">No invoices found.</td></tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}
''')

with open('templates/invoices/create.html', 'w', encoding='utf-8') as f:
    f.write('''{% extends "base/base.html" %}
{% block title %}Create Invoice - SimpleCRM{% endblock %}
{% block content %}
<div class="card">
    <h1>Create Invoice</h1>
    <form method="POST" action="{{ url_for('invoices.create_invoice') }}">
        <div class="form-group" style="margin-bottom: 1rem;">
            <label>Customer</label>
            <select name="customer_id" required style="width:100%; padding:0.5rem;">
                <option value="">-- Select Customer --</option>
                {% for c in customers %}<option value="{{ c.id }}">{{ c.first_name }} {{ c.last_name }}</option>{% endfor %}
            </select>
        </div>
        <div style="display: flex; gap: 1rem; margin-bottom: 1rem;">
            <div class="form-group" style="flex:1;">
                <label>Invoice Date</label><input type="date" name="invoice_date" required style="width:100%; padding:0.5rem;">
            </div>
            <div class="form-group" style="flex:1;">
                <label>Due Date</label><input type="date" name="due_date" required style="width:100%; padding:0.5rem;">
            </div>
        </div>
        <div class="form-group" style="margin-bottom: 1rem;">
            <label>Status</label>
            <select name="status" style="width:100%; padding:0.5rem;">
                <option value="Draft">Draft</option>
                <option value="Sent">Sent</option>
            </select>
        </div>
        
        <h3>Products</h3>
        <div id="product-rows">
            <div class="product-row" style="display: flex; gap: 1rem; margin-bottom: 0.5rem;">
                <select name="product_id[]" style="flex-grow: 1; padding:0.5rem;">
                    <option value="">-- Select Product --</option>
                    {% for p in products %}<option value="{{ p.id }}">{{ p.name }} - ${{ p.price }}</option>{% endfor %}
                </select>
                <input type="number" name="quantity[]" placeholder="Qty" step="1" min="1" style="width: 100px; padding:0.5rem;">
            </div>
        </div>
        <button type="button" class="btn" id="add-row" style="margin-bottom: 1rem; background: var(--border-color);">+ Add Another Product</button>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem; margin-top:1rem;">
            <div class="form-group"><label>Discount ($)</label><input type="number" name="discount" step="0.01" value="0.00" style="width:100%; padding:0.5rem;"></div>
            <div class="form-group"><label>Tax (%)</label><input type="number" name="tax" step="0.01" value="0.00" style="width:100%; padding:0.5rem;"></div>
        </div>
        
        <button type="submit" class="btn btn-primary" style="margin-top:1rem;">Generate Invoice</button>
    </form>
</div>
{% endblock %}
{% block scripts %}
<script>
document.getElementById('add-row').addEventListener('click', function() {
    const row = document.querySelector('.product-row').cloneNode(true);
    row.querySelector('select').value = '';
    row.querySelector('input').value = '';
    document.getElementById('product-rows').appendChild(row);
});
</script>
{% endblock %}
''')

with open('templates/invoices/view.html', 'w', encoding='utf-8') as f:
    f.write('''{% extends "base/base.html" %}
{% block title %}Invoice {{ invoice.invoice_number }} - SimpleCRM{% endblock %}
{% block content %}
<div class="card" style="display: flex; justify-content: space-between;">
    <div>
        <h1>Invoice: {{ invoice.invoice_number }}</h1>
        <p><strong>Status:</strong> {{ invoice.status }}</p>
        <p><strong>Date:</strong> {{ invoice.invoice_date }}</p>
        <p><strong>Due:</strong> {{ invoice.due_date }}</p>
    </div>
    <div style="text-align: right;">
        <h3>Bill To:</h3>
        <p>{{ customer.first_name }} {{ customer.last_name }}</p>
        <p>{{ customer.company }}</p>
        <button class="btn btn-primary" onclick="window.print()" style="margin-top:1rem;">Print Invoice</button>
    </div>
</div>
<div class="card">
    <table style="width: 100%; border-collapse: collapse; margin-top:1rem;">
        <thead>
            <tr style="border-bottom: 2px solid var(--border-color); text-align: left;">
                <th style="padding: 0.75rem;">Item</th><th style="padding: 0.75rem;">Qty</th><th style="padding: 0.75rem;">Price</th><th style="padding: 0.75rem;">Total</th>
            </tr>
        </thead>
        <tbody>
            {% for item in invoice.get('items', []) %}
            <tr style="border-bottom: 1px solid var(--border-color);">
                <td style="padding: 0.75rem;">{{ item.product_name }}</td>
                <td style="padding: 0.75rem;">{{ item.quantity }}</td>
                <td style="padding: 0.75rem;">${{ "%.2f"|format(item.price) }}</td>
                <td style="padding: 0.75rem;">${{ "%.2f"|format(item.line_total) }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    <div style="margin-top: 1.5rem; text-align: right;">
        <p><strong>Subtotal:</strong> ${{ "%.2f"|format(invoice.subtotal) }}</p>
        <p><strong>Discount:</strong> -${{ "%.2f"|format(invoice.discount) }}</p>
        <p><strong>Tax:</strong> ${{ "%.2f"|format(invoice.tax_amount) }}</p>
        <h2 style="margin-top: 0.5rem;">Total: ${{ "%.2f"|format(invoice.total) }}</h2>
    </div>
</div>
{% endblock %}
''')

with open('templates/payments/list.html', 'w', encoding='utf-8') as f:
    f.write('''{% extends "base/base.html" %}
{% block title %}Payments - SimpleCRM{% endblock %}
{% block content %}
<div class="card" style="display: flex; justify-content: space-between; align-items: center;">
    <h1>Payments</h1>
    <a href="{{ url_for('payments.create_payment') }}" class="btn btn-primary">Record Payment</a>
</div>
<div class="card">
    <table style="width: 100%; border-collapse: collapse;">
        <thead>
            <tr style="border-bottom: 2px solid var(--border-color); text-align: left;">
                <th style="padding: 0.75rem;">Date</th>
                <th style="padding: 0.75rem;">Invoice</th>
                <th style="padding: 0.75rem;">Customer</th>
                <th style="padding: 0.75rem;">Method</th>
                <th style="padding: 0.75rem;">Amount</th>
            </tr>
        </thead>
        <tbody>
            {% for p in payments %}
            <tr style="border-bottom: 1px solid var(--border-color);">
                <td style="padding: 0.75rem;">{{ p.payment_date }}</td>
                <td style="padding: 0.75rem;">{{ p.invoice_number }}</td>
                <td style="padding: 0.75rem;">{{ p.customer_name }}</td>
                <td style="padding: 0.75rem;">{{ p.payment_method }}</td>
                <td style="padding: 0.75rem; font-weight:bold; color:var(--success-color);">+${{ "%.2f"|format(p.amount) }}</td>
            </tr>
            {% else %}
            <tr><td colspan="5" style="padding: 1rem; text-align: center;">No payments recorded.</td></tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}
''')

with open('templates/payments/create.html', 'w', encoding='utf-8') as f:
    f.write('''{% extends "base/base.html" %}
{% block title %}Record Payment - SimpleCRM{% endblock %}
{% block content %}
<div class="card">
    <h1>Record Payment</h1>
    <form method="POST" action="{{ url_for('payments.create_payment') }}">
        <div class="form-group" style="margin-bottom: 1rem;">
            <label>Invoice</label>
            <select name="invoice_id" required style="width:100%; padding:0.5rem;">
                <option value="">-- Select Invoice --</option>
                {% for i in invoices %}
                <option value="{{ i.id }}">{{ i.invoice_number }} (Total: ${{ "%.2f"|format(i.total) }})</option>
                {% endfor %}
            </select>
        </div>
        <div class="form-group" style="margin-bottom: 1rem;">
            <label>Customer</label>
            <select name="customer_id" required style="width:100%; padding:0.5rem;">
                <option value="">-- Select Customer --</option>
                {% for c in customers %}<option value="{{ c.id }}">{{ c.first_name }} {{ c.last_name }}</option>{% endfor %}
            </select>
        </div>
        <div class="form-group" style="margin-bottom: 1rem;">
            <label>Amount ($)</label>
            <input type="number" step="0.01" name="amount" required style="width:100%; padding:0.5rem;">
        </div>
        <div class="form-group" style="margin-bottom: 1rem;">
            <label>Payment Date</label>
            <input type="date" name="payment_date" required style="width:100%; padding:0.5rem;">
        </div>
        <div class="form-group" style="margin-bottom: 1rem;">
            <label>Method</label>
            <select name="payment_method" required style="width:100%; padding:0.5rem;">
                <option value="Card">Card</option>
                <option value="Bank Transfer">Bank Transfer</option>
                <option value="Cash">Cash</option>
                <option value="Other">Other</option>
            </select>
        </div>
        <button type="submit" class="btn btn-primary">Save Payment</button>
    </form>
</div>
{% endblock %}
''')

# --- UPDATE APP INIT ---
content = """import os
from flask import Flask, session
from config.settings import config
from app.utils.logger import setup_logger

def create_app(config_name='default'):
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config.from_object(config[config_name])
    setup_logger(app)
    os.makedirs(app.config['DATA_DIR'], exist_ok=True)
    
    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    from app.dashboard import bp as dashboard_bp
    app.register_blueprint(dashboard_bp)
    from app.users import bp as users_bp
    app.register_blueprint(users_bp)
    from app.customers import bp as customers_bp
    app.register_blueprint(customers_bp)
    from app.contacts import bp as contacts_bp
    app.register_blueprint(contacts_bp)
    from app.leads import bp as leads_bp
    app.register_blueprint(leads_bp)
    from app.opportunities import bp as opportunities_bp
    app.register_blueprint(opportunities_bp)
    from app.tasks import bp as tasks_bp
    app.register_blueprint(tasks_bp)
    from app.followups import bp as followups_bp
    app.register_blueprint(followups_bp)
    from app.products import bp as products_bp
    app.register_blueprint(products_bp)
    from app.sales import bp as sales_bp
    app.register_blueprint(sales_bp)
    from app.invoices import bp as invoices_bp
    app.register_blueprint(invoices_bp)
    from app.payments import bp as payments_bp
    app.register_blueprint(payments_bp)

    return app
"""
with open('app/__init__.py', 'w', encoding='utf-8') as f:
    f.write(content)

# --- UPDATE BASE TEMPLATE NAV ---
with open('templates/base/base.html', 'r', encoding='utf-8') as f:
    base_html = f.read()

if 'href="/invoices"' not in base_html:
    nav_link = '''<li><a href="{{ url_for('invoices.list_invoices') }}">Invoices</a></li>
                    <li><a href="{{ url_for('payments.list_payments') }}">Payments</a></li>
                    <!-- Future links will go here -->'''
    base_html = base_html.replace('<!-- Future links will go here -->', nav_link)
    with open('templates/base/base.html', 'w', encoding='utf-8') as f:
        f.write(base_html)
