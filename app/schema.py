from . import ma
from .models import Facility, Group, Person, InstrumentSession


class FacilitySchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Facility

facilitySchema = FacilitySchema()
facilitiesSchema = FacilitySchema(many=True)

class FacilityGroupSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Group

facilityGroupSchema = FacilityGroupSchema()
facilityGroupsSchema = FacilityGroupSchema(many=True)

class FacilityPersonSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Person

facilityPersonSchema = FacilityPersonSchema()
facilityPersonsSchema = FacilityPersonSchema(many=True)

class InstrumentSessionSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = InstrumentSession

instrumentSessionSchema = InstrumentSessionSchema()
instrumentSessionsSchema = InstrumentSessionSchema(many=True)