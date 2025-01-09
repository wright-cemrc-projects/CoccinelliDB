from marshmallow import fields

from . import ma
from .models import Project, Facility, Group, Person, Instrument, InstrumentSession, InstrumentIssue


class FacilitySchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Facility

facilitySchema = FacilitySchema()
facilitiesSchema = FacilitySchema(many=True)

class FacilityGroupSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Group
        include_relationships = True  # Include relationships in the schema
        load_instance = True
    persons_ids = fields.Method("get_persons_ids")

    def get_persons_ids(self, group):
        return [person.id for person in group.persons]

facilityGroupSchema = FacilityGroupSchema()
facilityGroupsSchema = FacilityGroupSchema(many=True)

class FacilityPersonSchema(ma.SQLAlchemyAutoSchema):
    primary_contact = ma.Boolean()
    class Meta:
        model = Person
        include_relationships = True
        load_instance = True

facilityPersonSchema = FacilityPersonSchema()
facilityPersonsSchema = FacilityPersonSchema(many=True)

class InstrumentSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Instrument
        include_fk = True
instrumentSchema = InstrumentSchema()
instrumentsSchema = InstrumentSchema(many=True)

class InstrumentSessionSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = InstrumentSession
        include_fk = True
instrumentSessionSchema = InstrumentSessionSchema()
instrumentSessionsSchema = InstrumentSessionSchema(many=True)

class ProjectSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Project
        include_fk = True
projectSchema = ProjectSchema()
projectsSchema = ProjectSchema(many=True)

class InstrumentIssueSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = InstrumentIssue
        include_fk = True
instrumentIssueSchema = InstrumentIssueSchema()
instrumentIssuesSchema = InstrumentIssueSchema(many=True)