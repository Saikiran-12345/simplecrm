"""
Enterprise API Layer Initialization
This module registers all sub-blueprints for the RESTful JSON API.
"""
from flask import Blueprint, jsonify

bp = Blueprint('api', __name__, url_prefix='/api/v1')

# Import and register sub-modules here
# Note: In a large enterprise app, we might use Flask-RESTful or Flask-Smorest,
# but we are building this purely with Flask primitives for maximum custom control.

@bp.route('/health', methods=['GET'])
def health_check():
    """
    API Health Check Endpoint
    Returns standard 200 OK if the API subsystem is operational.
    """
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0',
        'message': 'SimpleCRM Enterprise API is running'
    }), 200

from app.api import auth, customers, leads, opportunities, products, sales, invoices, payments, tasks, followups, notes, employees
