import re

def is_valid_email(email):
    if not email: return True # Optional field support
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(pattern, email) is not None

def is_valid_phone(phone):
    if not phone: return True
    # Strip common characters
    cleaned = re.sub(r'[\s\-\(\)\+]', '', phone)
    return cleaned.isdigit() and len(cleaned) >= 7

def validate_required(data_dict, required_keys):
    missing = [k for k in required_keys if not data_dict.get(k) or not str(data_dict.get(k)).strip()]
    if missing:
        return False, f"Missing required fields: {', '.join(missing)}"
    return True, ""
