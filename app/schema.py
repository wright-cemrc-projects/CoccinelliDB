from . import ma
from .models import FacilityModel, FacilityGroup

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

