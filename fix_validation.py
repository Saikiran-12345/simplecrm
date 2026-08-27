with open('app/customers/routes.py', 'r', encoding='utf-8') as f:
    c_routes = f.read()

validation_injection = """
        # Phase 23: Data Validation Hook
        from app.utils.validators import is_valid_email, validate_required
        is_valid, msg = validate_required(data, ['first_name'])
        if not is_valid:
            flash(msg, 'danger')
            return redirect(url_for('customers.create_customer'))
            
        if data.get('email') and not is_valid_email(data.get('email')):
            flash('Invalid email format provided.', 'danger')
            return redirect(url_for('customers.create_customer'))
"""

c_routes = c_routes.replace(
    "storage = get_customer_storage()",
    validation_injection + "\n        storage = get_customer_storage()"
)

with open('app/customers/routes.py', 'w', encoding='utf-8') as f:
    f.write(c_routes)
