import pytest
from app import create_app, db
from config import TestingConfig
import os
import tempfile

@pytest.fixture()
def app():
    app = create_app(TestingConfig)

    with app.app_context():
        db.create_all() 
    yield app

    with app.app_context():
        db.drop_all()

@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()