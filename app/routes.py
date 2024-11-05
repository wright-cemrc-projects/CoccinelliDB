from flask import Blueprint, render_template, jsonify, request
from flask_cors import CORS
from . import db
from .models import FacilityModel, FacilityGroup
from .schema import facilitySchema, facilitiesSchema, facilityGroupSchema, facilityGroupsSchema

main = Blueprint('main', __name__)
CORS(main)


@main.route('/')
def index():
    return "Hello, World!"

@main.route('/home', methods=['GET'])
def hello_world():
    return jsonify({"message": "Hello World"})

@main.route('/facility', methods=['GET'])
def get_facility_list():
    facility_list = db.session.execute(db.select(FacilityModel)).scalars()
    return facilitiesSchema.jsonify(facility_list)

@main.route('/facility/<int:id>', methods=['GET'])
def get_facility_by_id(id):
    facility_one = db.session.execute(db.select(FacilityModel).filter_by(id=id)).scalar_one()
    return facilitySchema.jsonify(facility_one)

@main.route('/facility', methods=['POST'])
def create_facility():
    name = request.json["name"]
    try:
        facility = FacilityModel(name)
        db.session.add(facility)
        db.session.commit()
        return jsonify({"message": "new facility created."})
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@main.route('/facility/<int:id>', methods=['POST'])
def update_facility(id):
    try:
        name = request.json["name"]
        facility = db.session.execute(db.select(FacilityModel).filter_by(id=id)).scalar_one()
        facility.name = name
        db.session.commit()
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@main.route('/facility/<int:id>', methods=['DELETE'])
def delete_facility(id):
    try:
        facility = db.session.execute(db.select(FacilityModel).filter_by(id=id)).scalar_one()
        db.session.delete(facility)
        db.session.commit()
        return jsonify({"message": f"{facility} got deleted."})
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@main.route('/group', methods=['POST'])
def create_group():
    try:
        name = request.json["name"]
        facility_id = request.json["facility_id"]
        group = FacilityGroup(name=name, facility_id=facility_id)
        db.session.add(group)
        db.session.commit()
    except Exception as err:
        return jsonify({"err": f"{err=}"})


@main.route('/group/<int:id>', methods=['GET'])
def get_group_by_id(id):
    try:
        group = db.get_or_404(FacilityGroup, id)
        return facilityGroupSchema.jsonify(group)
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@main.route('/group', methods=['GET'])
def get_group_list():
    try:
        group_list = db.session.execute(db.select(FacilityModel)).scalars()
        return facilityGroupsSchema.jsonify(group_list)
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@main.route('/group/<int:id>', methods=['POST'])
def updage_group(id):
    try:
        group = db.session.execute(db.select(FacilityGroup).filter_by(id=id)).scalar_one()
        if "name" in request.json:
            group.name = request.json["name"]
        if "facility_id" in request.json:
            group.facility_id = request.json["facility_id"]
        db.session.commit()
    except Exception as err:
        return jsonify({"err": f"{err=}"})    

@main.route('/group/<int:id>', methods=['DELETE'])
def delete_group(id):
    try:
        group = db.session.execute(db.select(FacilityGroup).filter_by(id=id)).scalar_one()
        db.session.delete(group)
        db.session.commit()
        return jsonify({"message", f"{group} got deleted."})
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@main.route('/person', methods=['POST'])
def create_person():
    pass

@main.route('/person/<int:id>', methods=['GET'])
def get_person_by_id(id):
    pass

@main.route('/person', methods=['GET'])
def get_person_list():
    pass

@main.route('/person/<int:id>', methods=['POST'])
def update_person(id):
    pass

@main.route('/person/<int:id>', methods=['POST'])
def deletePerson(id):
    pass