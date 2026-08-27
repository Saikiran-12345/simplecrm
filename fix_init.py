content = """import os
from flask import Flask, session
from config.settings import config
from app.utils.logger import setup_logger

def create_app(config_name='default'):
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Set up logger
    setup_logger(app)
    
    # Ensure data directory exists
    os.makedirs(app.config['DATA_DIR'], exist_ok=True)
    
    # Register blueprints
    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)
    
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from app.dashboard import bp as dashboard_bp
    app.register_blueprint(dashboard_bp)
    
    from app.users import bp as users_bp
    app.register_blueprint(users_bp)
    
    from app.customers import bp as customers_bp
    app.register_blueprint(customers_bp)

    from app.contacts import bp as contacts_bp
    app.register_blueprint(contacts_bp)

    from app.leads import bp as leads_bp
    app.register_blueprint(leads_bp)

    from app.opportunities import bp as opportunities_bp
    app.register_blueprint(opportunities_bp)

    from app.tasks import bp as tasks_bp
    app.register_blueprint(tasks_bp)

    from app.followups import bp as followups_bp
    app.register_blueprint(followups_bp)

    from app.products import bp as products_bp
    app.register_blueprint(products_bp)

    from app.sales import bp as sales_bp
    app.register_blueprint(sales_bp)

    return app
"""
with open('app/__init__.py', 'w', encoding='utf-8') as f:
    f.write(content)
