from flask import Blueprint
bp = Blueprint('opportunities', __name__)
from app.opportunities import routes
