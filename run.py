import os
from app import create_app

# Determine config from environment, fallback to default
config_name = os.getenv('FLASK_CONFIG', 'default')
app = create_app(config_name)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=app.config.get('DEBUG', False))
