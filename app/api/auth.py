"""
API Authentication Subsystem
Uses highly secure, time-expiring JSON Web Tokens (JWT) for stateless API authentication.
"""
from flask import request, jsonify, current_app, g
from functools import wraps
import jwt
from datetime import datetime, timedelta
from app.api import bp
from app.api.errors import unauthorized, forbidden
from app.utils.storage import BaseStorage
from werkzeug.security import check_password_hash

def generate_api_token(user_id, role, expires_in=3600):
    """Generates a JWT token for the given user configuration."""
    payload = {
        'user_id': user_id,
        'role': role,
        'exp': datetime.utcnow() + timedelta(seconds=expires_in),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, current_app.config.get('SECRET_KEY', 'fallback_secret'), algorithm='HS256')

def verify_api_token(token):
    """Verifies and decodes a JWT token."""
    try:
        payload = jwt.decode(token, current_app.config.get('SECRET_KEY', 'fallback_secret'), algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def api_login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return unauthorized('Missing or invalid Authorization header. Expected "Bearer <token>"')
            
        token = auth_header.split(' ')[1]
        payload = verify_api_token(token)
        if not payload:
            return unauthorized('Token is invalid or has expired.')
            
        g.api_user_id = payload.get('user_id')
        g.api_role = payload.get('role')
        return f(*args, **kwargs)
    return decorated

def api_role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not hasattr(g, 'api_role') or g.api_role not in roles:
                return forbidden(f'Insufficient permissions. Required one of: {", ".join(roles)}')
            return f(*args, **kwargs)
        return decorated
    return decorator

@bp.route('/auth/token', methods=['POST'])
def get_token():
    """
    Token Generation Endpoint
    Accepts application/json with username and password.
    Returns a short-lived JWT token for subsequent API calls.
    """
    data = request.get_json() or {}
    if 'username' not in data or 'password' not in data:
        return unauthorized('Must include username and password in JSON payload.')
        
    storage = BaseStorage(current_app.config['DATA_DIR'], 'users')
    users = storage.get_all_records()
    user = next((u for u in users if u.get('username') == data['username']), None)
    
    if not user or not check_password_hash(user.get('password_hash', ''), data['password']):
        return unauthorized('Invalid username or password.')
        
    if user.get('status') != 'Active':
        return unauthorized('User account is suspended or inactive.')
        
    token = generate_api_token(user['id'], user['role'])
    return jsonify({
        'token': token,
        'expires_in': 3600,
        'token_type': 'Bearer'
    })
