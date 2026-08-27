from flask import Blueprint
bp = Blueprint('custom_fields', __name__)
from app.custom_fields import routes
