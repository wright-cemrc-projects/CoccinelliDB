import string

from flask import Flask, g
from flask_security import Security, SQLAlchemyUserDatastore
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import login_user, current_user
import click
import os
from datetime import datetime
from sqlalchemy import MetaData, insert
from flask_marshmallow import Marshmallow
from sqlalchemy.testing.plugin.plugin_base import config
from flask_oidc import OpenIDConnect
from flask_cors import CORS
import config
from tests.test_routes import test_group, test_person
import secrets

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
oidc = None


class _DevOidcStub:
    """
    Stand-in for flask_oidc's OpenIDConnect, used when OIDC_ENABLED is False.
    Lets routes written against the real oidc object (@oidc.require_login,
    oidc.user_getinfo, etc.) keep working while OAuth is skipped locally.
    """

    def __init__(self, dev_email):
        self.dev_email = dev_email
        self.user_loggedin = True

    def require_login(self, view_func):
        return view_func

    def user_getfield(self, field):
        from .models import Person
        person = Person.query.filter_by(email=self.dev_email).first()
        return getattr(person, field, None) if person else None

    def user_getinfo(self, fields):
        from .models import Person
        person = Person.query.filter_by(email=self.dev_email).first()
        info = {
            "email": self.dev_email,
            "sub": "dev-local",
            "name": f"{person.first_name} {person.last_name}" if person else "Dev User",
        }
        return {field: info.get(field) for field in fields}

    def logout(self):
        pass


def _seed_dev_user(app, email):
    """
    Ensure a local Admin-rights Person exists for `email` so the OAuth
    bypass (OIDC_ENABLED=False) has a real, fully-authorized user to run
    requests as.
    """
    from .models import Person, Role

    with app.app_context():
        try:
            person = Person.query.filter_by(email=email).first()
            if not person:
                person = Person("Dev", "User", email, "dev-local")
                db.session.add(person)
                db.session.commit()

            admin_role = Role.query.filter_by(name="Admin").first()
            if not admin_role:
                admin_role = Role(name="Admin")
                db.session.add(admin_role)
                db.session.commit()

            if admin_role not in person.roles:
                person.roles.append(admin_role)
                db.session.commit()
        except Exception as exc:
            db.session.rollback()
            print(f"Skipping dev user seeding ({exc}); has `flask db upgrade` been run?")


def create_app(config_name=os.getenv('FLASK_ENV', 'development')):

    app = Flask(__name__)
    # secret key for signing the cookie and session
    secret_key = secrets.token_hex(24)

    app.config['SECRET_KEY'] = secret_key
    conf = config_map.get(config_name, config.DevelopmentConfig)

    app.config.from_object(conf)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    ma.init_app(app)

    global oidc
    if app.config.get("OIDC_ENABLED", True):
        app.config["OIDC_CLIENT_SECRETS"] = "./client_secrets.json"
        oidc = OpenIDConnect(app)
    else:
        dev_email = app.config.get("DEV_USER_EMAIL")
        _seed_dev_user(app, dev_email)
        oidc = _DevOidcStub(dev_email)

    CORS(app, supports_credentials=True, origins=["http://localhost:5173"])
   
    # Register routes (from routes/*)
    from routes.main_routes import main
    from routes.remote_api_routes import remote_api_bp
    from routes.login_routes import  login_bp
    from routes.user_routes import user
    from routes.dashboard_routes import dashboard_bp
    from routes.instrument_client_routes import instrument_client_bp
    from routes.tiltseries_routes import tiltseries_bp

    app.register_blueprint(main)
    app.register_blueprint(remote_api_bp)
    app.register_blueprint(login_bp)
    app.register_blueprint(user)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(instrument_client_bp)
    app.register_blueprint(tiltseries_bp)

    from .models import Group, Facility, Person, Role, Project, group_person
    user_datastore = SQLAlchemyUserDatastore(db, Person, Role)
    security = Security(app, user_datastore)

    @app.before_request
    def attach_current_user():
        if not app.config.get("OIDC_ENABLED", True):
            person = Person.query.filter_by(email=app.config.get("DEV_USER_EMAIL")).first()
            if person:
                g.person = person
                if not current_user.is_authenticated:
                    login_user(person)
            return

        if oidc.user_loggedin:
            email = oidc.user_getfield("email")
            person = Person.query.filter_by(email=email).first()
            if person:
                g.person = person

    @app.cli.command("create-roles")
    @click.argument("roles", nargs=-1)
    def create_roles(roles):
        for role_name in roles:
            role = Role(name=role_name)
            db.session.add(role)
        db.session.commit()
        print("Roles created successfully!")

    @app.cli.command("create-user")
    @click.argument("first_name")
    @click.argument("last_name")
    @click.argument("email")
    @click.argument("net_id")
    def create_user(first_name, last_name, email, net_id):
        person = Person(first_name, last_name, email, net_id)
        db.session.add(person)
        db.session.commit()

    @app.cli.command("assign-role")
    @click.argument("email")
    @click.argument("role_name")
    def assign_role(email, role_name):
        """Assign a role to a person by ID and role name."""
        person = Person.query.filter_by(email=email).first()
        if not person:
            click.echo(f" No person found with that email {email}.")
            return

        role = Role.query.filter_by(name=role_name).first()
        if not role:
            click.echo(f" Role '{role_name}' not found.")
            return

        if role in person.roles:
            click.echo(f" Person already has role '{role_name}'.")
        else:
            person.roles.append(role)
            db.session.commit()
            click.echo(f" Added role '{role_name}' to person ID {person.id}.")

    @app.cli.command("remove-role")
    @click.argument("email")
    @click.argument("role_name")
    def remove_role(email, role_name):
        person = Person.query.filter_by(email=email).first()
        if not person:
            click.echo(f" No person found with that email {email}.")
            return
        
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            click.echo(f" Role '{role_name}' not found.")
            return
        
        if role in person.roles:
            person.roles.remove(role)
            db.session.commit()
            click.echo(f" Role '{role_name}' remove from '{email}'.")
        else:
            click.echo(f"'{email}' does not have the role '{role_name}'.")

    @app.cli.command("create-facility")
    @click.argument("name")
    def create_facility(name):
        facility = Facility(name=name)
        db.session.add(facility)
        db.session.commit()

    @app.cli.command("create-group")
    @click.argument("name")
    def create_group(name):
        group = Group(name=name)
        db.session.add(group)
        db.session.commit()

    @app.cli.command("create-project")
    @click.argument("project_id")
    @click.argument("facility_id")
    def create_project(project_id, facility_id):
        project = Project(project_id)
        project.facility_id = facility_id
        db.session.add(project)
        db.session.commit()

    @app.cli.command("create-instrument-session")
    @click.argument("facility_id")
    @click.argument("instrument_id")
    @click.option("--project-id", default=None, help="Optional Project.id to link.")
    @click.option("--start-date", default=None, help="ISO 8601, defaults to now.")
    @click.option("--end-date", default=None, help="ISO 8601, defaults to unset.")
    def create_instrument_session(facility_id, instrument_id, project_id, start_date, end_date):
        from .models import InstrumentSession
        session = InstrumentSession(
            facility_id=facility_id,
            instrument_id=instrument_id,
            project_id=project_id,
            start_date=datetime.fromisoformat(start_date) if start_date else datetime.utcnow(),
            end_date=datetime.fromisoformat(end_date) if end_date else None,
        )
        db.session.add(session)
        db.session.commit()
        click.echo(f"Created InstrumentSession id={session.id}")

    @app.cli.command("create-collection")
    @click.argument("instrument_session_id")
    @click.option("--collection-type", default="Screening", help="Screening, SPA, or CryoET.")
    @click.option("--data-location", default=None, help="Path scanned for thumbnails/images.")
    @click.option("--start-date", default=None, help="ISO 8601, defaults to now.")
    @click.option("--end-date", default=None, help="ISO 8601, defaults to unset.")
    @click.option("--total-image-count", default=0, type=int)
    def create_collection(instrument_session_id, collection_type, data_location, start_date, end_date, total_image_count):
        from .models import Collection
        collection = Collection(
            instrument_session_id=instrument_session_id,
            collection_type=collection_type,
            data_location=data_location,
            start_date=datetime.fromisoformat(start_date) if start_date else datetime.utcnow(),
            end_date=datetime.fromisoformat(end_date) if end_date else None,
            total_image_count=total_image_count,
        )
        db.session.add(collection)
        db.session.commit()
        click.echo(f"Created Collection id={collection.id} linked to InstrumentSession id={instrument_session_id}")

    @app.cli.command("add-user-to-group")
    @click.argument("email")
    @click.argument("group")
    @click.argument("primary_contact")
    def add_user_to_group(email, group, primary_contact):
        ''' Create a linking record that adds a Person to a Group '''
        # Find the Person.id by email
        a_person = Person.query.filter_by(email=email).first()

        # Find the Group.id by 'group' name
        a_group = Group.query.filter_by(name=group).first()

        # Create a new group_person record to match those or throw an error.
        if (a_person and a_group):
            stmt = insert(group_person).values(group_id=a_group.id, person_id=a_person.id, primary_contact=bool(primary_contact))
            db.session.execute(stmt)
            db.session.commit()
        else:
            print("Unable to find person or group")

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
