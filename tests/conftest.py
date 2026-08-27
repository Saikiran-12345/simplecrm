import pytest
import os
import shutil
from app import create_app
from config.settings import config

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    # Create the app with testing config
    app = create_app('testing')
    
    yield app
    
    # Cleanup test data directory after each run
    test_data_dir = app.config['DATA_DIR']
    if os.path.exists(test_data_dir):
        shutil.rmtree(test_data_dir)

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test runner for the app's cli commands."""
    return app.test_cli_runner()

