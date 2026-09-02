import pytest
from app import create_app, db, _seed_dev_user
import os
import tempfile

@pytest.fixture()
def app():
    app = create_app('testing')

    with app.app_context():
        db.create_all()
        # create_app() already tried this, but the person/role tables didn't
        # exist yet at that point (this is a fresh in-memory DB, unlike dev.db
        # which already has them via `flask db upgrade`); seeding is
        # idempotent, so it's safe to redo now that the tables are there.
        _seed_dev_user(app, app.config.get("DEV_USER_EMAIL"))
    yield app

    with app.app_context():
        db.drop_all()

@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()