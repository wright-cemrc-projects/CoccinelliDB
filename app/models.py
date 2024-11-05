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


class FacilityModel(db.Model):
    """ Representation of a facility """
    __tablename__ = "facility"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(45), nullable=False, unique=True)
    group = db.relationship("FacilityGroup", backref="facility", lazy="dynamic")
    projects: Mapped[List["FacilityProject"]] = relationship(backref="facility")
    instruments: Mapped[List["FacilityInstrument"]] = relationship(backref="facility")
    sessions: Mapped[List["FacilityInstrumentSession"]] = relationship(backref="facility")

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"<Facility(name={self.name})>"

class FacilityGroup(db.Model):
    """ Representation of a lab group or organization """
    __tablename__ = "facility_group"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(45), nullable=False, unique=True)
    facility_id = db.Column(db.Integer, db.ForeignKey("facility.id"), unique=False, nullable=False)
    # facility = db.relationship("FacilityModel", back_populates="facility_group")
    person = db.relationship("FacilityPerson", backref="facility_group", lazy="dynamic")
    
    def __repr__(self):
        return f"<FacilityGroup(name={self.name})>"

class FacilityPerson(db.Model):
    """ Representation of an individual """
    __tablename__ = "facility_person"
    id = db.Column(db.Integer, primary_key=True)
    # group = db.relationship("FacilityGroup", back_populates="facility_person")
    group_id = db.Column(db.Integer, db.ForeignKey("facility_group.id"), unique=False, nullable=False)
    first_name = db.Column(db.String(45))
    last_name = db.Column(db.String(45))
    organization = db.Column(db.String(45), nullable=True)
    email = db.Column(db.String(45), unique=True)
    address1 = db.Column(db.String(45), nullable=True) 
    address2 = db.Column(db.String(45), nullable=True)
    state = db.Column(db.String(45), nullable=True)
    country = db.Column(db.String(45), nullable=True)
    telephone = db.Column(db.String(45), nullable=True)
    net_id = db.Column(db.String(45 ), unique=False)
    start_date = db.Column(db.DateTime, nullable=True) 
    end_date = db.Column(db.DateTime, nullable=True)

    @validates("email")
    def validate_email(self, key, email):
        if is_email(email, check_dns=True):
            return address
        raise ValueErrir("Invalid email!")

    def __repr__(self):
        return f"FacilityPerson(name={self.first_name} {self.last_name}, email={self.email})"
# Entries below using SQLAlchemy ORM configuration style with Declarative mappings with Mapped.
# https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html
# back_populates argument is to be used when we want data access in both directions from
# Example, from the FacilityProject back to the FacilityModel and vice versa.

class FacilityProject(db.Model):
    """ Representation of a research project """
    __tablename__ = "facility_project"
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.String(45))
    facility_id : Mapped[int] = mapped_column(ForeignKey("facility.id"))
    # facility : Mapped["FacilityModel"] = relationship(back_populates="projects")

class FacilityInstrument(db.Model):
    """ Representation of an instrument """
    __tablename__ = "facility_instrument"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(45))
    model = db.Column(db.String(45))
    facility_id : Mapped[int] = mapped_column(ForeignKey("facility.id"))
    # facility : Mapped["FacilityModel"] = relationship(back_populates="instruments")
    issues: Mapped[List["FacilityInstrumentIssue"]] = relationship(back_populates="facility_instrument")

class FacilityInstrumentIssue(db.Model):
    """ Representation of an instrument issue """
    __tablename__ = "facility_instrument_issue"
    id = db.Column(db.Integer, primary_key=True)
    instrument_offline = db.column(db.Boolean)
    issue_title = db.Column(db.String(45))
    issue_description = db.Column(db.String(45))
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    instrument_id : Mapped[int] = mapped_column(ForeignKey("facility_instrument.id"))
    facility_instrument : Mapped["FacilityInstrument"] = relationship(back_populates="issues")

class FacilityInstrumentSession(db.Model):
    """ Representation of a session of instrument use """
    __tablename__ = "facility_instrument_session"
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, primary_key=True)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    facility_id : Mapped[int] = mapped_column(ForeignKey("facility.id"))
    # facility : Mapped["FacilityModel"] = relationship(back_populates="instrument_sessions")

#class FacilitySessionPersonLink(db.Model):
#    """ Representation of many-to-many relationship between Session and Person tables """
#    __tablename__ = "session_person_link"
#    Q: how to setup this links to two different tables, FacilityInstrumentSession and FacilityPerson

class FacilityCollection(db.Model):
    """ Representation of a data collection that occurred duing an instrument session """
    __tablename__ = "facility_collection"
    id = db.Column(db.Integer, primary_key=True)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    data_location = db.Column(db.String(45))

class FacilityGridBox(db.Model):
    """ Representation of a grid box, an organize of grids in the facility storage """
    __tablename__ = "facility_grid_box"
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