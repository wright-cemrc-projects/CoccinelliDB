from __future__ import annotations
from . import db

from typing import List

from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import relationship
from sqlalchemy.orm import validates
from pyisemail import is_email


class Facility(db.Model):
    """ Representation of a facility """
    __tablename__ = "facility"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(45), nullable=False, unique=True)
    # Linked table [one Facility -> many Project(s)]
    projects: Mapped[List["Project"]] = relationship(back_populates="facility")
    # Linked table [one Facility -> many Instrument(s)]
    instruments: Mapped[List["Instrument"]] = relationship(back_populates="facility")
    # Linked table [one Facility -> many InstrumentSessions(s)]
    sessions: Mapped[List["InstrumentSession"]] = relationship(back_populates="facility")

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"<Facility(name={self.name})>"

# Linked table [many Group -> many Person(s)]
group_person = db.Table('group_person',
                        db.Column('group_id', db.Integer, db.ForeignKey('group.id')),
                        db.Column('person_id', db.Integer, db.ForeignKey('person.id')))

class Group(db.Model):
    """ Representation of a lab group or organization """
    __tablename__ = "group"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(45), nullable=False, unique=True)
    # Linked table [one Group -> many Person(s)]
    persons = db.relationship("Person", backref="group", lazy="dynamic", secondary=group_person)

    def __repr__(self):
        return f"<Group(name={self.name})>"

class Person(db.Model):
    """ Representation of an individual """
    __tablename__ = "person"
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(45))
    last_name = db.Column(db.String(45))
    organization = db.Column(db.String(45), nullable=True)
    email = db.Column(db.String(45), unique=True)
    address1 = db.Column(db.String(45), nullable=True) 
    address2 = db.Column(db.String(45), nullable=True)
    state = db.Column(db.String(45), nullable=True)
    country = db.Column(db.String(45), nullable=True)
    telephone = db.Column(db.String(45), nullable=True)
    net_id = db.Column(db.String(45 ), unique=True)
    start_date = db.Column(db.DateTime, nullable=True) 
    end_date = db.Column(db.DateTime, nullable=True)

    def __init__(self, first_name, last_name, email, net_id):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.net_id = net_id

    @validates("email")
    def validate_email(self, key, email):
        if is_email(email, check_dns=True):
            return email
        raise ValueError("Invalid email!")

    def __repr__(self):
        return f"Person(name={self.first_name} {self.last_name}, email={self.email})"
    
# Entries below using SQLAlchemy ORM configuration style with Declarative mappings with Mapped.
# https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html
# back_populates argument is to be used when we want data access in both directions from
# Example, from the FacilityProject back to the FacilityModel and vice versa.

class Project(db.Model):
    """ Representation of a research project """
    __tablename__ = "project"
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.String(45))
    facility_id : Mapped[int] = mapped_column(ForeignKey("facility.id"))
    facility : Mapped["Facility"] = relationship(back_populates="projects")
    # Linked table [one FacilityProject -> many FacilityInstrumentSessions]
    sessions: Mapped[List["InstrumentSession"]] = relationship(back_populates="project")

class Instrument(db.Model):
    """ Representation of an instrument """
    __tablename__ = "instrument"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(45))
    model = db.Column(db.String(45))
    # Linked table [one Facility -> many FacilityInstrument(s)]
    facility_id : Mapped[int] = mapped_column(ForeignKey("facility.id"))
    facility : Mapped["Facility"] = relationship(back_populates="instruments")
    # Linked table [one Instrument -> many InstrumentIssue(s)]
    issues: Mapped[List["InstrumentIssue"]] = relationship(back_populates="instrument")
    # Linked table [one Instrument -> many InstrumentSession(s)]
    sessions: Mapped[List["InstrumentSession"]] = relationship(back_populates="instrument")

class InstrumentIssue(db.Model):
    """ Representation of an instrument issue """
    __tablename__ = "instrument_issue"
    id = db.Column(db.Integer, primary_key=True)
    instrument_offline = db.Column(db.Boolean)
    issue_title = db.Column(db.String(45))
    issue_description = db.Column(db.String(45))
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    # Linked table [one Instrument -> many InstrumentIssue(s)]
    instrument_id : Mapped[int] = mapped_column(ForeignKey("instrument.id"))
    instrument : Mapped["Instrument"] = relationship(back_populates="issues")

class InstrumentSession(db.Model):
    """ Representation of a session of instrument use """
    __tablename__ = "instrument_session"
    id = db.Column(db.Integer, primary_key=True)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    # Linked table [one Facility-> many InstrumentSession(s)]
    facility_id : Mapped[int] = mapped_column(ForeignKey("facility.id"))
    facility : Mapped["Facility"] = relationship(back_populates="sessions")
    # Linked table [one Project-> many InstrumentSession(s)]
    project_id : Mapped[int] = mapped_column(ForeignKey("project.id"))
    project : Mapped["Project"] = relationship(back_populates="sessions")
    # Linked table [one Instrument-> many InstrumentSession(s)]
    instrument_id : Mapped[int] = mapped_column(ForeignKey("instrument.id"))
    instrument : Mapped["Instrument"] = relationship(back_populates="sessions")
    # Linked table [one InstrumentSession-> many InstrumentCollection(s)]
    collections: Mapped[List["Collection"]] = relationship(back_populates="instrument_session")

# This is setup for additional flexibility for how we define persons being in a session,
#  and includes fields tied to the person:
#   'onsite': is this person an onsite user or remote?
#   'role' : is this person an operator, trainee, or other?
#   'remote_access_level' : 
# Linked table [many FacilityInstrumentSession -> many FacilityPerson(s)]
session_person_link = db.Table(
    'session_person_link',
    db.Column('session_id', db.Integer, db.ForeignKey('instrument_session.id')),
    db.Column('person_id', db.Integer, db.ForeignKey('person.id')),
    db.Column('onsite', db.Boolean),
    db.Column('role', db.String(45)),
    db.Column('remote_access_level', db.String(45))
)

class Collection(db.Model):
    """ Representation of a data collection that occurred duing an instrument session """
    __tablename__ = "collection"
    id = db.Column(db.Integer, primary_key=True)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    data_location = db.Column(db.String(45))
    # Linked table [one FacilityInstrumentSession-> many FacilityInstrumentCollection(s)]
    instrument_session_id : Mapped[int] = mapped_column(ForeignKey("instrument_session.id"))
    instrument_session : Mapped["InstrumentSession"] = relationship(back_populates="collections")

class GridBox(db.Model):
    """ Representation of a grid box, an organize of grids in the facility storage """
    __tablename__ = "grid_box"
    id = db.Column(db.Integer, primary_key=True)
    box_position = db.Column(db.String(45)) # is this correct
    box_label = db.Column(db.String(45))
    box_slot = db.Column(db.Integer) # what is the purpose
    bsl_level = db.Column(db.Integer) # 1 - 4
    date_prepared = db.Column(db.DateTime)
    grid_type = db.Column(db.String(45))
    blot_time_seconds = db.Column(db.Float)
    drain_time_seconds = db.Column(db.Float)
    blot_force = db.Column(db.Integer)
    falcon_type_location = db.Column(db.String(45))
    instrument = db.Column(db.String(45)) # could link to a facility instrument?
    comments = db.Column(db.String(45)) # may need a larger comment block
    box_status = db.Column(db.String(45)) # could be with options here
    # TODO: this table is missing linkages in the database.
    #  How does a GridBox (container of grids and indexing/storage of grids) relate to a sample (individual grid)?
    #  How does a GridBox or Grid relate to a data collection or instrument session?
    #  Where should we make these links and definitions?
