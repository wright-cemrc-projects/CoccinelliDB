from . import db

class FacilityModel(db.Model):
    __tablename__ = "facility"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(45), nullable=False, unique=True)
    group = db.relationship("FacilityGroup", back_populates="facility", lazy="dynamic")

class FacilityGroup(db.Model):
    __tablename__ = "facility_group"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(45), nullable=False)
    facility_id = db.Column(db.Integer, db.ForeignKey("facility.id"), unique=False, nullable=False)
    facility = db.relationship("FacilityModel", back_populates="facility_group")
    person = db.relationship("FacilityPerson", back_populates="facility_group", lazy="dynamic")

class FacilityPerson(db.Model):
    __tablename__ = "facility_person"
    id = db.Column(db.Integer, primary_key=True)
    group = db.relationship("FacilityGroup", back_populates="facility_person")
    group_id = db.Column(db.Integer, db.ForeignKey("facility_group.id"), unique=False, nullable=False)
    first_name = db.Column(db.String(45))
    last_name = db.Column(db.String(45))
    organization = db.Column(db.String(45))
    email = db.Column(db.String(45))
    address1 = db.Column(db.String(45)) 
    address2 = db.Column(db.String(45))
    state = db.Column(db.String(45))
    country = db.Column(db.String(45))
    telephone = db.Column(db.String(45))
    net_id = db.Column(db.String(45 ))
    start_date = db.Column(db.DateTime) 
    end_date = db.Column(db.DateTime)
