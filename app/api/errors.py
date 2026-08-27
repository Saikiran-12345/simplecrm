"""
API Error Handlers
Standardizes JSON error responses across the entire API surface.
"""
from flask import jsonify
from app.api import bp

def bad_request(message):
    response = jsonify({'error': 'bad request', 'message': message})
    response.status_code = 400
    return response

def unauthorized(message):
    response = jsonify({'error': 'unauthorized', 'message': message})
    response.status_code = 401
    return response

def forbidden(message):
    response = jsonify({'error': 'forbidden', 'message': message})
    response.status_code = 403
    return response

def not_found(message):
    response = jsonify({'error': 'not found', 'message': message})
    response.status_code = 404
    return response

@bp.errorhandler(400)
def bad_request_error(e):
    return bad_request(str(e))

@bp.errorhandler(401)
def unauthorized_error(e):
    return unauthorized(str(e))

@bp.errorhandler(403)
def forbidden_error(e):
    return forbidden(str(e))

@bp.errorhandler(404)
def not_found_error(e):
    return not_found(str(e))
    
@bp.errorhandler(500)
def internal_server_error(e):
    response = jsonify({'error': 'internal server error', 'message': 'An unexpected error occurred.'})
    response.status_code = 500
    return response
