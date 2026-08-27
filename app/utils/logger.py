import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger(app):
    """Configure the application logger."""
    log_dir = app.config.get('LOG_DIR')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(log_dir, 'simplecrm.log')
    
    # Set up rotating file handler (max 10MB per file, keep 5 backups)
    file_handler = RotatingFileHandler(log_file, maxBytes=10240000, backupCount=5)
    
    # Define log format
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    )
    file_handler.setFormatter(formatter)
    
    # Set log level based on debug mode
    if app.debug:
        file_handler.setLevel(logging.DEBUG)
        app.logger.setLevel(logging.DEBUG)
    else:
        file_handler.setLevel(logging.INFO)
        app.logger.setLevel(logging.INFO)

    app.logger.addHandler(file_handler)
    app.logger.info('SimpleCRM startup')

