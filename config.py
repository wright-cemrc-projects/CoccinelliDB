import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'no key set'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    INSTRUMENT_API_KEY = os.environ.get('INSTRUMENT_API_KEY') or 'dev-instrument-api-key'
    # Real OIDC login is required unless a config explicitly turns it off.
    OIDC_ENABLED = True
    DEV_USER_EMAIL = None

class DevelopmentConfig(Config):
    # SQLite database for development
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'dev.db')
    DEBUG = True
    # Skip the real OAuth flow locally; requests run as a seeded dev user instead.
    OIDC_ENABLED = False
    DEV_USER_EMAIL = 'dev-user@gmail.com'

class ProductionConfig(Config):
    DB_USERNAME = os.environ.get('DB_USERNAME') or 'no user'
    DB_PASSWORD = os.environ.get('DB_PASSWORD') or 'no password'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://' + DB_USERNAME + ':' + DB_PASSWORD + "@localhost/CoccinelliDB"
    DEBUG = True

class TestingConfig(Config):
    # SQLite database for testing (using in-memory database)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    TESTING = True
    # Same OAuth bypass as DevelopmentConfig: routes protected by roles_accepted
    # need a real authenticated user to test against, not just an open door.
    OIDC_ENABLED = False
    DEV_USER_EMAIL = 'test-admin@gmail.com'
