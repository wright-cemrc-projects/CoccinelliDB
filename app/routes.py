from flask import Blueprint, render_template, jsonify, request
from flask_cors import CORS
from . import db
from .models import *
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
def getFacilityList():
    facility_list = db.session.execute(db.select(FacilityModel)).scalars()
    return facilitiesSchema.jsonify(facility_list)

@main.route('/facility/<int:id>', methods=['GET'])
def getFacilityOne(id):
    facility_one = db.session.execute(db.select(FacilityGroup).filter_by(id=id)).scalar_one()
    return facilitySchema.jsonify(facility_one)

@main.route('/facility', methods=['POST'])
def createFacility():
    name = request.form("name")
    try:
        facility = FacilityGroup(name)
        db.session.add(facility)
        db.commit()
        return jsonify({"message": "new facility created."})
    except Exception as err:
        return jsonify({"err": err})

@main.route('/facility/<int:id>', methods=['DELETE'])
def deleteFacility(id):
    try:
        facility = db.session.execute(db.select(FacilityGroup).filter_by(id=id)).scalar_one()
        db.session.delete(facility)
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