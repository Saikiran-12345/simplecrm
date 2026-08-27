import os

# Create directories
os.makedirs('app/products', exist_ok=True)
os.makedirs('templates/products', exist_ok=True)
os.makedirs('app/sales', exist_ok=True)
os.makedirs('templates/sales', exist_ok=True)

# --- PRODUCTS BLUEPRINT ---
with open('app/products/__init__.py', 'w', encoding='utf-8') as f:
    f.write('''from flask import Blueprint
bp = Blueprint('products', __name__)
from app.products import routes
''')

with open('app/products/routes.py', 'w', encoding='utf-8') as f:
    f.write('''from flask import render_template, request, redirect, url_for, flash, current_app
from app.products import bp
from app.auth.utils import login_required
from app.utils.storage import BaseStorage

def get_storage():
    return BaseStorage(current_app.config['DATA_DIR'], 'products')

@bp.route('/products')
@login_required
def list_products():
    storage = get_storage()
    search_query = request.args.get('q', '').lower()
    all_products = storage.get_all_records()
    
    if search_query:
        products = [p for p in all_products if search_query in p.get('name', '').lower() or 
                    search_query in p.get('category', '').lower()]
    else:
        products = all_products
        
    return render_template('products/list.html', products=products, search_query=search_query)

@bp.route('/products/create', methods=['GET', 'POST'])
@login_required
def create_product():
    if request.method == 'POST':
        data = {
            'name': request.form.get('name'),
            'description': request.form.get('description'),
            'category': request.form.get('category'),
            'price': request.form.get('price', '0'),
            'quantity': request.form.get('quantity', '0'),
            'status': request.form.get('status', 'Active')
        }
        storage = get_storage()
        storage.create_record(data)
        flash('Product created successfully.', 'success')
        return redirect(url_for('products.list_products'))
        
    return render_template('products/create.html')

@bp.route('/products/<record_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(record_id):
    storage = get_storage()
    product = storage.get_record(record_id)
    if not product:
        flash('Product not found.', 'danger')
        return redirect(url_for('products.list_products'))
        
    if request.method == 'POST':
        data = {
            'name': request.form.get('name'),
            'description': request.form.get('description'),
            'category': request.form.get('category'),
            'price': request.form.get('price'),
            'quantity': request.form.get('quantity'),
            'status': request.form.get('status')
        }
        storage.update_record(record_id, data)
        flash('Product updated successfully.', 'success')
        return redirect(url_for('products.list_products'))
        
    return render_template('products/edit.html', product=product)

@bp.route('/products/<record_id>/delete', methods=['POST'])
@login_required
def delete_product(record_id):
    storage = get_storage()
    if storage.delete_record(record_id):
        flash('Product deleted successfully.', 'success')
    else:
        flash('Product not found.', 'danger')
    return redirect(url_for('products.list_products'))
''')

# --- SALES BLUEPRINT ---
with open('app/sales/__init__.py', 'w', encoding='utf-8') as f:
    f.write('''from flask import Blueprint
bp = Blueprint('sales', __name__)
from app.sales import routes
''')

with open('app/sales/routes.py', 'w', encoding='utf-8') as f:
    f.write('''from flask import render_template, request, redirect, url_for, flash, current_app, session
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
''')

# --- TEMPLATES ---
with open('templates/products/list.html', 'w', encoding='utf-8') as f:
    f.write('''{% extends "base/base.html" %}
{% block title %}Products - SimpleCRM{% endblock %}
{% block content %}
<div class="card" style="display: flex; justify-content: space-between; align-items: center;">
    <h1>Products</h1>
    <a href="{{ url_for('products.create_product') }}" class="btn btn-primary">Add Product</a>
</div>
<div class="card">
    <table style="width: 100%; border-collapse: collapse;">
        <thead>
            <tr style="border-bottom: 2px solid var(--border-color); text-align: left;">
                <th style="padding: 0.75rem;">Name</th>
                <th style="padding: 0.75rem;">Category</th>
                <th style="padding: 0.75rem;">Price</th>
                <th style="padding: 0.75rem;">Inventory</th>
                <th style="padding: 0.75rem;">Status</th>
                <th style="padding: 0.75rem;">Actions</th>
            </tr>
        </thead>
        <tbody>
            {% for p in products %}
            <tr style="border-bottom: 1px solid var(--border-color);">
                <td style="padding: 0.75rem; font-weight: 500;">{{ p.name }}</td>
                <td style="padding: 0.75rem;">{{ p.category }}</td>
                <td style="padding: 0.75rem;">${{ p.price }}</td>
                <td style="padding: 0.75rem; {% if p.quantity|float <= 5 %}color: var(--danger-color); font-weight:bold;{% endif %}">{{ p.quantity }}</td>
                <td style="padding: 0.75rem;">{{ p.status }}</td>
                <td style="padding: 0.75rem; display: flex; gap: 0.5rem;">
                    <a href="{{ url_for('products.edit_product', record_id=p.id) }}" style="color: var(--primary-color); text-decoration: none;">Edit</a>
                    <form method="POST" action="{{ url_for('products.delete_product', record_id=p.id) }}" style="display:inline;">
                        <button type="submit" style="background:none; border:none; color:var(--danger-color); cursor:pointer; text-decoration:underline;">Delete</button>
                    </form>
                </td>
            </tr>
            {% else %}
            <tr><td colspan="6" style="padding: 1rem; text-align: center;">No products found.</td></tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}
''')

product_form = '''
<div class="form-group" style="margin-bottom: 1rem;"><label>Product Name</label><input type="text" name="name" value="{{ product.name if product else '' }}" required style="width:100%; padding:0.5rem;"></div>
<div class="form-group" style="margin-bottom: 1rem;"><label>Description</label><textarea name="description" style="width:100%; padding:0.5rem;">{{ product.description if product else '' }}</textarea></div>
<div class="form-group" style="margin-bottom: 1rem;"><label>Category</label><input type="text" name="category" value="{{ product.category if product else '' }}" style="width:100%; padding:0.5rem;"></div>
<div class="form-group" style="margin-bottom: 1rem;"><label>Price ($)</label><input type="number" step="0.01" name="price" value="{{ product.price if product else '0.00' }}" required style="width:100%; padding:0.5rem;"></div>
<div class="form-group" style="margin-bottom: 1rem;"><label>Inventory Quantity</label><input type="number" name="quantity" value="{{ product.quantity if product else '0' }}" required style="width:100%; padding:0.5rem;"></div>
<div class="form-group" style="margin-bottom: 1rem;"><label>Status</label><select name="status" style="width:100%; padding:0.5rem;">
    <option value="Active" {% if product and product.status == 'Active' %}selected{% endif %}>Active</option>
    <option value="Inactive" {% if product and product.status == 'Inactive' %}selected{% endif %}>Inactive</option>
</select></div>
'''

with open('templates/products/create.html', 'w', encoding='utf-8') as f:
    f.write('{% extends "base/base.html" %}{% block content %}<div class="card"><h1>Add Product</h1><form method="POST">' + product_form + '<button class="btn btn-primary">Save</button></form></div>{% endblock %}')

with open('templates/products/edit.html', 'w', encoding='utf-8') as f:
    f.write('{% extends "base/base.html" %}{% block content %}<div class="card"><h1>Edit Product</h1><form method="POST">' + product_form + '<button class="btn btn-primary">Save</button></form></div>{% endblock %}')


with open('templates/sales/list.html', 'w', encoding='utf-8') as f:
    f.write('''{% extends "base/base.html" %}
{% block title %}Sales - SimpleCRM{% endblock %}
{% block content %}
<div class="card" style="display: flex; justify-content: space-between; align-items: center;">
    <h1>Sales</h1>
    <a href="{{ url_for('sales.create_sale') }}" class="btn btn-primary">Create Sale</a>
</div>
<div class="card">
    <table style="width: 100%; border-collapse: collapse;">
        <thead>
            <tr style="border-bottom: 2px solid var(--border-color); text-align: left;">
                <th style="padding: 0.75rem;">Date</th>
                <th style="padding: 0.75rem;">Customer</th>
                <th style="padding: 0.75rem;">Status</th>
                <th style="padding: 0.75rem;">Total</th>
                <th style="padding: 0.75rem;">Actions</th>
            </tr>
        </thead>
        <tbody>
            {% for s in sales %}
            <tr style="border-bottom: 1px solid var(--border-color);">
                <td style="padding: 0.75rem;">{{ s.sales_date }}</td>
                <td style="padding: 0.75rem;">{{ s.customer_name }}</td>
                <td style="padding: 0.75rem;">{{ s.status }}</td>
                <td style="padding: 0.75rem;">${{ "%.2f"|format(s.total) }}</td>
                <td style="padding: 0.75rem;">
                    <a href="{{ url_for('sales.view_sale', record_id=s.id) }}" style="color: var(--primary-color); text-decoration: none;">View</a>
                </td>
            </tr>
            {% else %}
            <tr><td colspan="5" style="padding: 1rem; text-align: center;">No sales found.</td></tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}
''')

with open('templates/sales/create.html', 'w', encoding='utf-8') as f:
    f.write('''{% extends "base/base.html" %}
{% block title %}Create Sale - SimpleCRM{% endblock %}
{% block content %}
<div class="card">
    <h1>Create Sale</h1>
    <form method="POST" action="{{ url_for('sales.create_sale') }}">
        <div class="form-group" style="margin-bottom: 1rem;">
            <label>Customer</label>
            <select name="customer_id" required style="width:100%; padding:0.5rem;">
                <option value="">-- Select Customer --</option>
                {% for c in customers %}
                <option value="{{ c.id }}">{{ c.first_name }} {{ c.last_name }}</option>
                {% endfor %}
            </select>
        </div>
        <div class="form-group" style="margin-bottom: 1rem;">
            <label>Date</label>
            <input type="date" name="sales_date" required style="width:100%; padding:0.5rem;">
        </div>
        
        <h3>Products</h3>
        <div id="product-rows">
            <div class="product-row" style="display: flex; gap: 1rem; margin-bottom: 0.5rem;">
                <select name="product_id[]" style="flex-grow: 1; padding:0.5rem;">
                    <option value="">-- Select Product --</option>
                    {% for p in products %}
                    <option value="{{ p.id }}">{{ p.name }} - ${{ p.price }} (In Stock: {{ p.quantity }})</option>
                    {% endfor %}
                </select>
                <input type="number" name="quantity[]" placeholder="Qty" step="1" min="1" style="width: 100px; padding:0.5rem;">
            </div>
        </div>
        <button type="button" class="btn" id="add-row" style="margin-bottom: 1rem; background: var(--border-color);">+ Add Another Product</button>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem; margin-top:1rem;">
            <div class="form-group">
                <label>Discount ($)</label>
                <input type="number" name="discount" step="0.01" value="0.00" style="width:100%; padding:0.5rem;">
            </div>
            <div class="form-group">
                <label>Tax (%)</label>
                <input type="number" name="tax" step="0.01" value="0.00" style="width:100%; padding:0.5rem;">
            </div>
        </div>
        
        <button type="submit" class="btn btn-primary" style="margin-top:1rem;">Complete Sale</button>
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

with open('templates/sales/view.html', 'w', encoding='utf-8') as f:
    f.write('''{% extends "base/base.html" %}
{% block title %}Sale Details - SimpleCRM{% endblock %}
{% block content %}
<div class="card" style="display: flex; justify-content: space-between; align-items: flex-start;">
    <div>
        <h1>Sale #{{ sale.id[:8] }}</h1>
        <p><strong>Customer:</strong> {{ customer_name }}</p>
        <p><strong>Date:</strong> {{ sale.sales_date }}</p>
        <p><strong>Status:</strong> {{ sale.status }}</p>
    </div>
    <a href="{{ url_for('sales.list_sales') }}" class="btn" style="background: var(--border-color);">Back to Sales</a>
</div>
<div class="card">
    <h2>Order Items</h2>
    <table style="width: 100%; border-collapse: collapse; margin-top:1rem;">
        <thead>
            <tr style="border-bottom: 2px solid var(--border-color); text-align: left;">
                <th style="padding: 0.75rem;">Product</th>
                <th style="padding: 0.75rem;">Price</th>
                <th style="padding: 0.75rem;">Qty</th>
                <th style="padding: 0.75rem;">Total</th>
            </tr>
        </thead>
        <tbody>
            {% for item in sale.items %}
            <tr style="border-bottom: 1px solid var(--border-color);">
                <td style="padding: 0.75rem;">{{ item.product_name }}</td>
                <td style="padding: 0.75rem;">${{ "%.2f"|format(item.price) }}</td>
                <td style="padding: 0.75rem;">{{ item.quantity }}</td>
                <td style="padding: 0.75rem;">${{ "%.2f"|format(item.line_total) }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    <div style="margin-top: 1.5rem; text-align: right;">
        <p><strong>Subtotal:</strong> ${{ "%.2f"|format(sale.subtotal) }}</p>
        <p><strong>Discount:</strong> -${{ "%.2f"|format(sale.discount) }}</p>
        <p><strong>Tax ({{ sale.tax_rate }}%):</strong> ${{ "%.2f"|format(sale.tax_amount) }}</p>
        <h3 style="margin-top: 0.5rem; color: var(--primary-color);">Total: ${{ "%.2f"|format(sale.total) }}</h3>
    </div>
</div>
{% endblock %}
''')

# --- UPDATE APP INIT ---
with open('app/__init__.py', 'r', encoding='utf-8') as f:
    content = f.read()

if 'app.register_blueprint(products_bp)' not in content:
    content = content.replace(
        'return app',
        "    from app.products import bp as products_bp\n    app.register_blueprint(products_bp)\n\n    from app.sales import bp as sales_bp\n    app.register_blueprint(sales_bp)\n\n    return app"
    )
    with open('app/__init__.py', 'w', encoding='utf-8') as f:
        f.write(content)

# --- UPDATE BASE TEMPLATE NAV ---
with open('templates/base/base.html', 'r', encoding='utf-8') as f:
    base_html = f.read()

if 'href="/products"' not in base_html:
    nav_link = '''<li><a href="{{ url_for('products.list_products') }}">Products</a></li>
                    <li><a href="{{ url_for('sales.list_sales') }}">Sales</a></li>
                    <!-- Future links will go here -->'''
    base_html = base_html.replace('<!-- Future links will go here -->', nav_link)
    with open('templates/base/base.html', 'w', encoding='utf-8') as f:
        f.write(base_html)
