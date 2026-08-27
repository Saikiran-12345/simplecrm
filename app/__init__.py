import os
from flask import Flask, session
from config.settings import config
from app.utils.logger import setup_logger

def create_app(config_name='default'):
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config.from_object(config[config_name])
    setup_logger(app)
    os.makedirs(app.config['DATA_DIR'], exist_ok=True)
    
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
    from app.invoices import bp as invoices_bp
    app.register_blueprint(invoices_bp)
    from app.payments import bp as payments_bp
    app.register_blueprint(payments_bp)
    from app.notes import bp as notes_bp
    app.register_blueprint(notes_bp)
    from app.reports import bp as reports_bp
    app.register_blueprint(reports_bp)
    from app.analytics import bp as analytics_bp
    app.register_blueprint(analytics_bp)

    
    
    from app.employees import bp as employees_bp
    app.register_blueprint(employees_bp)
    from app.rbac import bp as rbac_bp
    app.register_blueprint(rbac_bp)
    from app.settings import bp as settings_bp
    app.register_blueprint(settings_bp)
    from app.audit import bp as audit_bp
    app.register_blueprint(audit_bp)

    
    from app.search import bp as search_bp
    app.register_blueprint(search_bp)
    from app.notifications import bp as notif_bp
    app.register_blueprint(notif_bp)
    
    
    from app.api import bp as api_bp
    app.register_blueprint(api_bp)
    
    from app.automations import bp as automations_bp
    app.register_blueprint(automations_bp)
    from app.custom_fields import bp as custom_fields_bp
    app.register_blueprint(custom_fields_bp)
    from app.matrix_reports import bp as matrix_reports_bp
    app.register_blueprint(matrix_reports_bp)
    @app.context_processor



    def inject_settings():
        from app.utils.storage import BaseStorage
        storage = BaseStorage(app.config['DATA_DIR'], 'settings')
        
        settings = {r.get('key'): r.get('value') for r in storage.get_all_records()}
        
        unread_count = 0
        if 'username' in session:
            n_storage = BaseStorage(app.config['DATA_DIR'], 'notifications')
            unread_count = len([n for n in n_storage.get_all_records() if n.get('user') == session['username'] and not n.get('is_read')])
            
        
        custom_fields = {}
        try:
            cf_storage = BaseStorage(app.config['DATA_DIR'], 'custom_fields')
            cfs = cf_storage.get_all_records()
            for f in cfs:
                mod = f.get('module')
                if mod not in custom_fields: custom_fields[mod] = []
                custom_fields[mod].append(f)
        except Exception:
            pass
            
        return dict(global_settings=settings, unread_notifications=unread_count, custom_fields=custom_fields)


        
    return app

