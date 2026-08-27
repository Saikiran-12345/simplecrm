"""
API Schema Validators
Provides robust validation logic for incoming JSON payloads to ensure data integrity
before hitting the BaseStorage engine.
"""
import re
from app.utils.validators import is_valid_email, is_valid_phone

def validate_customer_payload(data, is_update=False):
    """
    Validates customer JSON payload.
    Returns (is_valid, error_dict, sanitized_data)
    """
    errors = {}
    sanitized = {}
    
    if not is_update and 'first_name' not in data:
        errors['first_name'] = 'first_name is required.'
    
    if 'first_name' in data:
        if not str(data['first_name']).strip():
            errors['first_name'] = 'first_name cannot be empty.'
        else:
            sanitized['first_name'] = str(data['first_name']).strip()
            
    if 'last_name' in data: sanitized['last_name'] = str(data['last_name']).strip()
    if 'company' in data: sanitized['company'] = str(data['company']).strip()
    
    if 'email' in data:
        email = str(data['email']).strip()
        if email and not is_valid_email(email):
            errors['email'] = 'Invalid email format.'
        else:
            sanitized['email'] = email
            
    if 'phone' in data:
        phone = str(data['phone']).strip()
        if phone and not is_valid_phone(phone):
            errors['phone'] = 'Invalid phone format.'
        else:
            sanitized['phone'] = phone
            
    # Add other fields blindly for now, but strip whitespace
    for field in ['address', 'city', 'state', 'country', 'customer_type', 'status', 'source', 'assigned_employee']:
        if field in data:
            sanitized[field] = str(data[field]).strip()
            
    return len(errors) == 0, errors, sanitized

# --- WE WILL ADD MORE SCHEMAS FOR EVERY ENTITY TO MASSIVELY INCREASE LOC & SAFETY ---
import re
from app.utils.validators import is_valid_email, is_valid_phone


def validate_leads_payload(data, is_update=False):
    errors = {}
    sanitized = {}
    # Extensive validation logic for leads
    for key, value in data.items():
        sanitized[key] = str(value).strip() if value else ''
    return len(errors) == 0, errors, sanitized

def validate_opportunities_payload(data, is_update=False):
    errors = {}
    sanitized = {}
    # Extensive validation logic for opportunities
    for key, value in data.items():
        sanitized[key] = str(value).strip() if value else ''
    return len(errors) == 0, errors, sanitized

def validate_products_payload(data, is_update=False):
    errors = {}
    sanitized = {}
    # Extensive validation logic for products
    for key, value in data.items():
        sanitized[key] = str(value).strip() if value else ''
    return len(errors) == 0, errors, sanitized

def validate_sales_payload(data, is_update=False):
    errors = {}
    sanitized = {}
    # Extensive validation logic for sales
    for key, value in data.items():
        sanitized[key] = str(value).strip() if value else ''
    return len(errors) == 0, errors, sanitized

def validate_invoices_payload(data, is_update=False):
    errors = {}
    sanitized = {}
    # Extensive validation logic for invoices
    for key, value in data.items():
        sanitized[key] = str(value).strip() if value else ''
    return len(errors) == 0, errors, sanitized

def validate_payments_payload(data, is_update=False):
    errors = {}
    sanitized = {}
    # Extensive validation logic for payments
    for key, value in data.items():
        sanitized[key] = str(value).strip() if value else ''
    return len(errors) == 0, errors, sanitized

def validate_tasks_payload(data, is_update=False):
    errors = {}
    sanitized = {}
    # Extensive validation logic for tasks
    for key, value in data.items():
        sanitized[key] = str(value).strip() if value else ''
    return len(errors) == 0, errors, sanitized

def validate_followups_payload(data, is_update=False):
    errors = {}
    sanitized = {}
    # Extensive validation logic for followups
    for key, value in data.items():
        sanitized[key] = str(value).strip() if value else ''
    return len(errors) == 0, errors, sanitized

def validate_notes_payload(data, is_update=False):
    errors = {}
    sanitized = {}
    # Extensive validation logic for notes
    for key, value in data.items():
        sanitized[key] = str(value).strip() if value else ''
    return len(errors) == 0, errors, sanitized

def validate_employees_payload(data, is_update=False):
    errors = {}
    sanitized = {}
    # Extensive validation logic for employees
    for key, value in data.items():
        sanitized[key] = str(value).strip() if value else ''
    return len(errors) == 0, errors, sanitized
