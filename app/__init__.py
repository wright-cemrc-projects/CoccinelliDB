import string

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import click
from sqlalchemy import MetaData
from flask_marshmallow import Marshmallow
from sqlalchemy.testing.plugin.plugin_base import config

import config
from tests.test_routes import test_group, test_person

naming_convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

config_map = {
    'development': config.DevelopmentConfig,
    'testing': config.TestingConfig,
    'production': config.ProductionConfig
}

db = SQLAlchemy(metadata=MetaData(naming_convention=naming_convention))
migrate = Migrate()
ma = Marshmallow()

def create_app(config_name="development"):
    app = Flask(__name__)

    conf = config_map.get(config_name, config.DevelopmentConfig)

    app.config.from_object(conf)
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    ma.init_app(app)

    # Register routes (from routes.py)
    from .routes import main, api_bp
    app.register_blueprint(main)
    app.register_blueprint(api_bp)
    
    from .models import Group, Facility, Person

    @app.cli.command("create-facility")
    @click.argument("name")
    def create_facility(name):
        facility = Facility(name=name)
        db.session.add(facility)
        db.session.commit()

    @app.cli.command("create-group")
    @click.argument("name")
    @click.argument("facility_id")
    def create_group(name):
        group = Group(name=name)
        db.session.add(group)
        db.session.commit()

    @app.cli.command("delete-group")
    @click.argument("id")
    def delete_group(id):
        group = db.session.execute(db.select(Group).filter_by(id=id)).scalar_one()
        db.session.delete(group)
        db.session.commit()

    @app.cli.command("load-test-group")
    def load_test_group():
        if config_name == "development":
            # A group named test_group if the flag that test group data has been loaded
            test_flag = db.session.execute(db.select(Group).filter_by(name="test_group")).first()
            if test_flag:
                print("test group data is already loaded.")
                return
            test_group_flag = Group(name="test_group")
            db.session.add(test_group_flag)
            lowercase_alphabet = list(string.ascii_lowercase)
            # test group data is [a_group, z_group]
            test_group_list = [letter + "_group" for letter in lowercase_alphabet]
            for group_name in test_group_list:
                group = Group(name=group_name)
                db.session.add(group)
            db.session.commit()
            print("test group data successfully loaded.")

    @app.cli.command("load-test-person")
    def load_test_person():
        if config_name == "development":
            # A person named test_person if the flag that test person data has been loaded
            test_flag = db.session.execute(db.select(Person).filter_by(first_name="test")).first()
            if test_flag:
                print("test person data is already loaded.")
                return
            test_person_flag = Person(first_name="test", last_name="person", email="test@gmail.com", net_id="123456")
            db.session.add(test_person_flag)
            lowercase_alphabet = list(string.ascii_lowercase)
            # test person data is [a_person, z_person]
            for letter in lowercase_alphabet:
                person = Person(first_name=letter, last_name="person", email=f"{letter}_test@gmail.com", net_id=f"{letter}123456")
                db.session.add(person)
            db.session.commit()
            print("test person data successfully loaded.")


    return app
