from flask import render_template, request, redirect, url_for, flash, current_app
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
