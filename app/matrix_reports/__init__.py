from flask import Blueprint
bp = Blueprint('matrix_reports', __name__)
from app.matrix_reports import routes
