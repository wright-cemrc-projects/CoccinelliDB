from marshmallow import Schema, fields, post_dump

from . import ma
from .models import Project, Facility, Group, Person, Instrument, InstrumentSession, InstrumentIssue, session_person_link, db


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

    instrument = fields.Nested("InstrumentSchema", only=["id", "name"])

    @post_dump
    def add_person_details(self, data, **kwargs):
        """ Attach onsite, role, and remote_access_level from session_person_link """
        session_id = data.get("id")
        if session_id:
            links = db.session.execute(
                db.select(session_person_link).filter_by(session_id=session_id)
            ).fetchall()

            persons_data = []
            for link in links:
                persons_data.append({
                    "person_id": link.person_id,  # Needed for frontend mapping
                    "onsite": link.onsite,
                    "role": link.role,
                    "remote_access_level": link.remote_access_level
                })
            data["persons"] = persons_data  # ✅ Attach required fields only

        return data

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

## Simple JSON response schema that can be returned by an API.
class SessionQuerySchema(Schema):
    id = fields.Int()
    start_time = fields.DateTime()
    end_time = fields.DateTime()
    netid = fields.String()
    email = fields.String()
    remote_access_allowed = fields.Bool()

## TODO: get a list of above as well for a Schema.
