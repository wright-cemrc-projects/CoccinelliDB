from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import click
from sqlalchemy import MetaData
from flask_marshmallow import Marshmallow
from sqlalchemy.testing.plugin.plugin_base import config

import config

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
    from .routes import main
    app.register_blueprint(main)
    
    from .models import Group, Facility

    @app.cli.command("create-facility")
    @click.argument("name")
    def create_facility(name):
        facility = Facility(name=name)
        db.session.add(facility)
        db.session.commit()

    @app.cli.command("create-group")
    @click.argument("name")
    @click.argument("facility_id")
    def create_group(name, facility_id):
        group = Group(name=name, facility_id=facility_id)
        db.session.add(group)
        db.session.commit()

    @app.cli.command("delete-group")
    @click.argument("id")
    def delete_group(id):
        group = db.session.execute(db.select(Group).filter_by(id=id)).scalar_one()
        db.session.delete(group)
        db.session.commit()

    return app
