from . import ma
from .models import *

class FacilitySchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = FacilityModel

facilitySchema = FacilitySchema()
facilitiesSchema = FacilitySchema(many=True)