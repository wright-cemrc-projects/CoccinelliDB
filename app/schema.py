from . import ma
from .models import FacilityModel, FacilityGroup, FacilityPerson


class FacilitySchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = FacilityModel

facilitySchema = FacilitySchema()
facilitiesSchema = FacilitySchema(many=True)

class FacilityGroupSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = FacilityGroup

facilityGroupSchema = FacilityGroupSchema()
facilityGroupsSchema = FacilityGroupSchema(many=True)

class FacilityPersonSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = FacilityPerson

facilityPersonSchema = FacilityPersonSchema()
facilityPersonsSchema = FacilityPersonSchema(many=True)