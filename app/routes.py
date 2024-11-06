from flask import Blueprint, render_template, jsonify, request
from flask_cors import CORS
from . import db
from .models import FacilityModel, FacilityGroup, FacilityPerson
from .schema import facilitySchema, facilitiesSchema, facilityGroupSchema, facilityGroupsSchema, facilityPersonSchema, facilityPersonsSchema

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
        return jsonify({"message": f"{facility} got updated"})
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
        return jsonify({"message": f"new group {name} created."})
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
def update_group(id):
    try:
        group = db.session.execute(db.select(FacilityGroup).filter_by(id=id)).scalar_one()
        if "name" in request.json:
            group.name = request.json["name"]
        if "facility_id" in request.json:
            group.facility_id = request.json["facility_id"]
        db.session.commit()
        return jsonify({"message": f"{group} got updated"})
    except Exception as err:
        return jsonify({"err": f"{err=}"})    

@main.route('/group/<int:id>', methods=['DELETE'])
def delete_group(id):
    try:
        group = db.session.execute(db.select(FacilityGroup).filter_by(id=id)).scalar_one()
        db.session.delete(group)
        db.session.commit()
        return jsonify({"message": f"{group} got deleted."})
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@main.route('/person', methods=['POST'])
def create_person():
    try:
        first_name = request.json["first_name"]
        last_name = request.json["last_name"]
        net_id = request.json["net_id"]
        email = request.json["email"]
        person = FacilityPerson(first_name, last_name, net_id, email)
        if "group_id" in request.json:
            person.group_id = request.json["group_id"]
        if "address1" in request.json:
            person.address1 = request.json["address1"]
        if "address2" in request.json:
            person.address2 = request.json["address2"]
        if "organization" in request.json:
            person.organization = request.json["organization"]
        if "state" in request.json:
            person.state = request.json["state"]
        if "telephone" in request.json:
            person.telephone = request.json["telephone"]
        if "start_date" in request.json:
            person.start_date = request.json["start_date"]
        if "end_date" in request.json:
            person.end_date = request.json["end_date"]
        db.session.add(person)
        db.session.commit()
        return jsonify({"message": f"{person} created."})
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@main.route('/person/<int:id>', methods=['GET'])
def get_person_by_id(id):
    try:
        person = db.get_or_404(FacilityPerson, id)
        return facilityPersonSchema.jsonify(person)
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@main.route('/person', methods=['GET'])
def get_person_list():
    try:
        person_list = db.session.execute(db.select(FacilityPerson)).scalars()
        return facilityPersonsSchema.jsonify(person_list)
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@main.route('/person/<int:id>', methods=['POST'])
def update_person(id):
    try:
        person = db.session.execute(db.select(FacilityGroup).filter_by(id=id)).scalar_one()
        if "first_name" in request.json:
            person.first_name = request.json["first_name"]
        if "last_name" in request.json:
            person.last_name = request.json["last_name"]
        if "organization" in request.json:
            person.organization = request.json["organization"]
        if "email" in request.json:
            person.email = request.json["email"]
        if "state" in request.json:
            person.state = request.json["state"]
        if "address1" in request.json:
            person.address1 = request.json["address1"]
        if "address2" in request.json:
            person.address2 = request.json["address2"]
        if "country" in request.json:
            person.country = request.json["country"]
        if "telephone" in request.json:
            person.telephone = request.json["telephone"]
        if "net_id" in request.json:
            person.net_id = request.json["net_id"]
        if "start_date" in request.json:
            person.start_date = request.json["start_date"]
        if "end_date" in request.json:
            person.end_date = request.json["end_date"]
        db.session.commit()
        return jsonify({"message": f"{person} got updated"})
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@main.route('/person/<int:id>', methods=['POST'])
def delete_person(id):
    try:
        person = db.session.execute(db.select(FacilityGroup).filter_by(id=id)).scalar_one()
        db.session.delete(person)
        db.session.commit()
        return jsonify({"message": f"{person} got deleted."})
    except Exception as err:
        return jsonify({"err": f"{err=}"})