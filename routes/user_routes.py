from datetime import datetime
import logging
from flask import Blueprint, request, jsonify

logger = logging.getLogger(__name__)
from flask_security import roles_accepted
from sqlalchemy import or_
from sqlalchemy import func, asc, desc
from app import db
from app.models import Facility, Group, Person, group_person, Role
from app.schema import facilitiesSchema, facilitySchema, facilityGroupSchema, facilityGroupsSchema, roleSchema, rolesSchema, \
    facilityPersonSchema, facilityPersonsSchema
from app.services.project_import_service import find_or_create_person

user = Blueprint('user', __name__)

@roles_accepted('Admin')
@user.route('/api/facilities', methods=['GET'])
def get_facility_list():
    search_query = request.args.get("name_like", "")
    facility_list = []
    if search_query:
        facility_list = Facility.query.filter(Facility.name.ilike(f"%{search_query}%")).all()
    else:
        facility_list = Facility.query.all()

    return facilitiesSchema.jsonify(facility_list)

@roles_accepted('Admin')
@user.route('/api/facilities/<int:id>', methods=['GET'])
def get_facility_by_id(id):
    facility_one = db.session.execute(db.select(Facility).filter_by(id=id)).scalar_one()
    return facilitySchema.jsonify(facility_one)

@roles_accepted('Admin')
@user.route('/api/facilities', methods=['POST'])
def create_facility():
    name = request.json["name"]
    try:
        facility = Facility(name)
        db.session.add(facility)
        db.session.commit()
        db.session.flush()
        return jsonify({"message": "new facility created."})
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@roles_accepted('Admin')
@user.route('/api/facilities/<int:id>', methods=['PATCH'])
def update_facility(id):
    try:
        name = request.json["name"]
        facility = db.session.execute(db.select(Facility).filter_by(id=id)).scalar_one()
        facility.name = name
        db.session.commit()
        return jsonify({"message": f"{facility} got updated"})
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@roles_accepted('Admin')
@user.route('/api/facilities/<int:id>', methods=['DELETE'])
def delete_facility(id):
    try:
        facility = db.session.execute(db.select(Facility).filter_by(id=id)).scalar_one()
        db.session.delete(facility)
        db.session.commit()
        return jsonify({"message": f"{facility} got deleted."})
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@roles_accepted('Admin')
@user.route('/api/groups', methods=['POST'])
def create_group():
    try:
        name = request.json["name"]
        group = Group(name=name)
        db.session.add(group)
        db.session.commit()
        return jsonify({"message": f"new group {name} created."})
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@roles_accepted('Admin')
@user.route('/api/groups/<int:id>', methods=['GET'])
def get_group_by_id(id):
    try:
        group = db.get_or_404(Group, id)
        return facilityGroupSchema.jsonify(group)
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@roles_accepted('Admin')
@user.route('/api/groups', methods=['GET'])
def get_group_list():
    try:
        name_like = request.args.get("name_like")
        query = db.session.query(Group)

        if name_like:
            query = query.filter(
                Group.name.ilike(f"%{name_like}%"),
            )
        return facilityGroupsSchema.jsonify(query.all())
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@roles_accepted('Admin')
@user.route('/api/groups/<int:id>', methods=['PATCH'])
def update_group(id):
    try:
        group = db.session.execute(db.select(Group).filter_by(id=id)).scalar_one()
        if "name" in request.json:
            group.name = request.json["name"]
        if "persons" in request.json:
            persons_data = request.json["persons"]
            new_persons_set = set(person["id"] for person in persons_data)
            old_persons_set = set([person.id for person in group.persons])
            add_persons = new_persons_set.difference(old_persons_set)
            delete_persons = old_persons_set.difference(new_persons_set)

            for person_id in add_persons:
                person = db.session.execute(db.select(Person).filter_by(id=person_id)).scalar_one()
                group.persons.append(person)
            for person_id in delete_persons:
                person = db.session.execute(db.select(Person).filter_by(id=person_id)).scalar_one()
                group.persons.remove(person)
            for person_data in persons_data:
                stmt = (
                    group_person.update()
                    .where(group_person.c.group_id == group.id)
                    .where(group_person.c.person_id == person_data["id"])
                    .values(primary_contact=person_data.get("primary_contact", False))
                )
                db.session.execute(stmt)
        db.session.commit()
        return jsonify({"message": f"{group} got updated"})
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@roles_accepted('Admin')
@user.route('/api/groups/<int:id>', methods=['DELETE'])
def delete_group(id):
    try:
        group = db.session.execute(db.select(Group).filter_by(id=id)).scalar_one()
        db.session.delete(group)
        db.session.commit()
        return jsonify({"message": f"{group} got deleted."})
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@roles_accepted('Admin')
@user.route('/api/roles', methods=['POST'])
def create_roles():
    try:
        name = request.json["name"]
        if "description" in request.json:
            description = request.json["description"]
        role = Group(name=name, description=description)
        db.session.add(role)
        db.session.commit()
        return jsonify({"message": f"new role {name} created."})
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@roles_accepted('Admin')
@user.route("/api/roles", methods=["GET"])
def get_roles():
    roles = Role.query.all()
    return rolesSchema.jsonify(roles)

@roles_accepted('Admin')
@user.route("/api/roles/<int:id>")
def get_role_by_id(id):
    try:
        role = db.get_or_404(Role, id)
        return roleSchema.jsonify(role)
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@roles_accepted('Admin')
@user.route('/api/roles/<int:id>', methods=['PATCH'])
def update_role(id):
    try:
        name = request.json["name"]
        description = request.json["description"]
        role = db.session.execute(db.select(Role).filter_by(id=id)).scalar_one()
        role.name = name
        role.description = description
        db.session.commit()
        return jsonify({"message": f"{role} got updated"})
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@roles_accepted('Admin')
@user.route('/api/roles/<int:id>', methods=['DELETE'])
def delete_role(id):
    try:
        role = db.session.execute(db.select(Role).filter_by(id=id)).scalar_one()
        db.session.delete(role)
        db.session.commit()
        return jsonify({"message": f"{role} got deleted."})
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@roles_accepted('Admin')
@user.route('/api/persons', methods=['POST'])
def create_person():
    try:
        date_format = "%Y-%m-%dT%H:%M:%S"

        # Get required arguments for initializer
        first_name = None
        if "first_name" in request.json:
            first_name = request.json["first_name"]
        last_name = None
        if "last_name" in request.json:
            last_name = request.json["last_name"]
        net_id = None
        if "net_id" in request.json:
            net_id = request.json["net_id"]
        email = None
        if "email" in request.json:
            email = request.json["email"]

        if (first_name and last_name and net_id and email) :
            person = Person(first_name = first_name, last_name = last_name, net_id = net_id, email = email)
        else:
            raise Exception('Missing arguments: first_name, last_name, net_id, and email')

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
            person.start_date = datetime.fromisoformat(request.json["start_date"])
        if "end_date" in request.json:
            person.end_date = datetime.fromisoformat(request.json["end_date"])
        role_ids = request.json.get("roles", [])
        if role_ids:
            roles = Role.query.filter(Role.id.in_(role_ids)).all()
            person.roles = roles
        db.session.add(person)
        db.session.commit()
        return jsonify({"message": f"{person} created."})
    except Exception as err:
        db.session.rollback()
        logger.error("create_person failed: %s", err, exc_info=True)
        return jsonify({"err": str(err)}), 400

@roles_accepted('Admin')
@user.route('/api/persons/find_or_create', methods=['POST'])
def find_or_create_person_route():
    """Get-or-create a person matched by email or net_id, for idempotent bulk import.

    Unlike POST /api/persons, an existing match is not an error here — the
    existing person is returned so re-running an import over the same rows
    links to the same person instead of creating a duplicate. net_id is
    optional (unlike POST /api/persons) since not every imported person, e.g.
    an outside collaborator, has one; email is always required as the fallback
    identity.
    """
    try:
        result = find_or_create_person(
            first_name=request.json.get("first_name"),
            last_name=request.json.get("last_name"),
            email=request.json.get("email"),
            net_id=request.json.get("net_id"),
            organization=request.json.get("organization"),
            address1=request.json.get("address1"),
            address2=request.json.get("address2"),
            state=request.json.get("state"),
            country=request.json.get("country"),
            telephone=request.json.get("telephone"),
        )
        db.session.commit()
        verb = "created" if result.created else "matched existing"
        return jsonify({
            "id": result.record.id,
            "created": result.created,
            "message": f"{verb} person {result.record}.",
        })
    except ValueError as err:
        db.session.rollback()
        return jsonify({"error": str(err)}), 400
    except Exception as err:
        db.session.rollback()
        logger.error("find_or_create_person_route failed: %s", err, exc_info=True)
        return jsonify({"error": str(err)}), 400

@roles_accepted('Admin')
@user.route('/api/persons/<int:id>', methods=['GET'])
def get_person_by_id(id):
    try:
        person = db.get_or_404(Person, id)
        return facilityPersonSchema.jsonify(person)
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@roles_accepted('Admin')
@user.route('/api/groups/<int:id>/persons', methods=['GET'])
def get_person_by_group(id):
    try:
        group = Group.query.get_or_404(id)
        persons = db.session.execute(
            db.select(
                Person.id,
                Person.first_name,
                Person.last_name,
                Person.email,
                group_person.c.primary_contact
            ).join(group_person).filter(group_person.c.group_id == group.id)
        ).all()

        return facilityPersonsSchema.jsonify(persons)
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@roles_accepted('Admin')
@user.route('/api/persons', methods=['GET'])
def get_person_list():
    try:
        query = Person.query
        full_name_like = request.args.get("full_name_like")

        sorter_fields = request.args.get("_sort", "").split(",")
        sorter_orders = request.args.get("_order", "asc").split(",")
        if full_name_like:
            filter_value = ''.join(full_name_like.lower().split())

            full_name_expr = func.lower(func.replace(Person.first_name + Person.last_name, " ", ""))

            query = query.filter(full_name_expr.contains(filter_value))

        allowed_fields = {"first_name", "last_name", "email", "net_id"}
        for i, field in enumerate(sorter_fields):
            field = field.strip()
            order = sorter_orders[i].strip() if i < len(sorter_orders) else "asc"
            if field in allowed_fields:
                sort_column = getattr(Person, field)
                query = query.order_by(asc(sort_column) if order == "asc" else desc(sort_column))
        persons = query.all()
        return facilityPersonsSchema.jsonify(persons)

    except Exception as err:
        print(err)
        return jsonify({"err": f"{err=}"})

@roles_accepted('Admin')
@user.route('/api/persons/<int:id>', methods=['PATCH'])
def update_person(id):
    try:
        date_format = "%Y-%m-%dT%H:%M:%S"
        person = db.session.execute(db.select(Person).filter_by(id=id)).scalar_one()
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
            person.start_date = datetime.fromisoformat(request.json["start_date"])
        if "end_date" in request.json:
            person.end_date = datetime.fromisoformat(request.json["end_date"])
        db.session.commit()
        return jsonify({"message": f"{person} got updated."})
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@roles_accepted('Admin')
@user.route('/api/persons/<int:id>', methods=['DELETE'])
def delete_person(id):
    try:
        person = db.session.execute(db.select(Person).filter_by(id=id)).scalar_one()
        db.session.delete(person)
        db.session.commit()
        return jsonify({"message": f"{person} got deleted."})
    except Exception as err:
        return jsonify({"err": f"{err=}"})