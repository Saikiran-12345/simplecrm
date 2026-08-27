from flask import Blueprint
bp = Blueprint('followups', __name__)
from app.followups import routes
