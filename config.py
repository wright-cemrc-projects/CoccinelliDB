import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'no key set'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevelopmentConfig(Config):
    # SQLite database for development
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'dev.db')

class TestingConfig(Config):
    # SQLite database for testing (using in-memory database)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    TESTING = True
