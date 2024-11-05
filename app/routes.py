from flask import Blueprint, render_template, jsonify, request
from flask_cors import CORS
from . import db
from .models import FacilityModel
from .schema import facilitySchema, facilitiesSchema

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

@main.route('/facility/<int:id>', methods=['DELETE'])
def delete_facility(id):
    try:
        facility = db.session.execute(db.select(FacilityModel).filter_by(id=id)).scalar_one()
        facility_dict = dict(facility)
        db.session.delete(facility)
        db.session.commit()
        return jsonify({"message": f"facility {facility_dict["name"]} got deleted."})
    except Exception as err:
        return jsonify(err)

# @main.route('/group', methods=['POST'])
# def createGroup():
#     pass

# @main.route()
# def getGroup():
#     pass

# @main.route()
# def listGroup():
#     pass

# @main.route()
# def updageGroup():
#     pass

# @main.route()
# def deleteGroup():
#     pass

# @main.route()
# def createPerson():
#     pass

# @main.route()
# def getPerson():
#     pass

# @main.route()
# def listPerson():
#     pass

# @main.route()
# def updatePerson():
#     pass

# @main.route()
# def deletePerson():
#     pass